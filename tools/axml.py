"""Binary manifest/package transforms for the supported external APK."""
import hashlib
import struct
import zipfile
import zlib
from pathlib import Path

OLD = 'com.community.mbox.in.geobypass'
NEW = 'com.community.mbox.in.popupfree'
assert len(OLD) == len(NEW)
NO = 0xffffffff
U16 = lambda b, p: struct.unpack_from('<H', b, p)[0]
U32 = lambda b, p: struct.unpack_from('<I', b, p)[0]

def read_length(b, p, utf8):
    if utf8:
        v = b[p]; p += 1
        if v & 128: v = ((v & 127) << 8) | b[p]; p += 1
    else:
        v = U16(b, p); p += 2
        if v & 0x8000: v = ((v & 0x7fff) << 16) | U16(b, p); p += 2
    return v, p

def length(v, utf8):
    if utf8:
        return bytes([v]) if v < 128 else bytes([(v >> 8) | 128, v & 255])
    return struct.pack('<H', v) if v < 32768 else struct.pack('<HH', (v >> 16) | 0x8000, v & 65535)

def patch_manifest(xml, label='MovieBox'):
    chunks=[]; p=U16(xml,2)
    while p < len(xml):
        size=U32(xml,p+4)
        if size < 8: raise ValueError('Invalid AXML chunk')
        chunks.append(xml[p:p+size]); p+=size
    pool=next(c for c in chunks if U16(c,0)==1)
    header=U16(pool,2); count=U32(pool,8); style_count=U32(pool,12)
    flags=U32(pool,16); start=U32(pool,20); style_start=U32(pool,24)
    utf8=bool(flags & 0x100); strings=[]
    for i in range(count):
        pos=start+U32(pool,header+i*4)
        n,pos=read_length(pool,pos,utf8)
        if utf8:
            n,pos=read_length(pool,pos,True)
            text=pool[pos:pos+n].decode('utf-8')
        else: text=pool[pos:pos+n*2].decode('utf-16le')
        strings.append(text.replace(OLD,NEW))
    def index(text):
        if text not in strings: strings.append(text)
        return strings.index(text)
    provider=index('provider'); android=index('http://schemas.android.com/apk/res/android')
    name=index('name'); authorities=index('authorities'); exported=index('exported'); order=index('initOrder')
    class_name=index('local.popupguard.GuardProvider'); authority=index(NEW+'.popupguard.init')
    test_label=index(label)
    data=bytearray(); offsets=[]
    for text in strings:
        offsets.append(len(data)); raw=text.encode('utf-8' if utf8 else 'utf-16le')
        n=len(text.encode('utf-16le'))//2
        data+=length(n,utf8)
        if utf8:data+=length(len(raw),True)
        data+=raw+(b'\0' if utf8 else b'\0\0')
    data+=b'\0'*((-len(data))%4)
    style_offsets=pool[header+count*4:header+(count+style_count)*4]
    styles=pool[style_start:] if style_start else b''
    string_start=header+(len(strings)+style_count)*4
    new_style_start=string_start+len(data) if style_start else 0
    new_pool=bytearray(pool[:header])
    struct.pack_into('<I',new_pool,4,string_start+len(data)+len(styles))
    struct.pack_into('<I',new_pool,8,len(strings))
    struct.pack_into('<I',new_pool,16,flags & ~1)  # appended entries are not sorted
    struct.pack_into('<II',new_pool,20,string_start,new_style_start)
    new_pool+=b''.join(struct.pack('<I',v) for v in offsets)+style_offsets+data+styles
    resource=next(c for c in chunks if U16(c,0)==0x180)
    ids=list(struct.unpack('<'+'I'*((len(resource)-8)//4),resource[8:]))
    while len(ids)<=max(name,authorities,exported,order):ids.append(0)
    for k,v in [(name,0x01010003),(authorities,0x01010018),(exported,0x01010010),(order,0x0101001a)]:
        if ids[k] not in (0,v):raise ValueError('Unexpected attribute resource ID')
        ids[k]=v
    new_resource=struct.pack('<HHI',0x180,8,8+len(ids)*4)+struct.pack('<'+'I'*len(ids),*ids)
    def attr(key,value,kind):
        return struct.pack('<IIIHBBI',android,key,value if kind==3 else NO,8,0,kind,value)
    attrs=b''.join([attr(name,class_name,3),attr(authorities,authority,3),attr(exported,0,0x12),attr(order,0x7fffffff,0x10)])
    new_start=struct.pack('<HHIII',0x102,16,36+len(attrs),0,NO)+struct.pack('<IIHHHHHH',NO,provider,20,20,4,0,0,0)+attrs
    new_end=struct.pack('<HHIII',0x103,16,24,0,NO)+struct.pack('<II',NO,provider)
    out=[]; inserted=False
    for c in chunks:
        kind=U16(c,0)
        if kind==1:c=bytes(new_pool)
        elif kind==0x180:c=new_resource
        elif kind==0x102 and strings[U32(c,20)]=='application':
            c=bytearray(c)
            attr_start=16+U16(c,24); attr_size=U16(c,26); attr_count=U16(c,28)
            for j in range(attr_count):
                pos=attr_start+j*attr_size
                if strings[U32(c,pos+4)]=='label':
                    struct.pack_into('<I',c,pos+8,test_label)
                    c[pos+15]=3
                    struct.pack_into('<I',c,pos+16,test_label)
            c=bytes(c)
        elif kind==0x103 and strings[U32(c,20)]=='application':
            out.extend([new_start,new_end]);inserted=True
        out.append(c)
    if not inserted:raise ValueError('Application closing element not found')
    body=b''.join(out)
    return struct.pack('<HHI',3,8,8+len(body))+body

def replace_package(data):
    return data.replace(OLD.encode(),NEW.encode()).replace(OLD.encode('utf-16le'),NEW.encode('utf-16le'))


def manifest_summary(xml):
    """Read only the package, labels and declarations needed to verify a build."""
    chunks = []
    cursor = U16(xml, 2)
    while cursor < len(xml):
        size = U32(xml, cursor + 4)
        if size < 8 or cursor + size > len(xml):
            raise ValueError('Malformed binary manifest chunk')
        chunks.append(xml[cursor:cursor + size])
        cursor += size
    pool = next(chunk for chunk in chunks if U16(chunk, 0) == 1)
    header, count, flags, start = U16(pool, 2), U32(pool, 8), U32(pool, 16), U32(pool, 20)
    utf8 = bool(flags & 0x100)
    strings = []
    for i in range(count):
        pos = start + U32(pool, header + i * 4)
        length_value, pos = read_length(pool, pos, utf8)
        if utf8:
            length_value, pos = read_length(pool, pos, True)
            strings.append(pool[pos:pos + length_value].decode('utf-8'))
        else:
            strings.append(pool[pos:pos + length_value * 2].decode('utf-16le'))
    def attributes(chunk):
        result = {}
        begin, width, number = 16 + U16(chunk, 24), U16(chunk, 26), U16(chunk, 28)
        for i in range(number):
            pos = begin + width * i
            key, raw, kind, value = strings[U32(chunk, pos + 4)], U32(chunk, pos + 8), chunk[pos + 15], U32(chunk, pos + 16)
            if kind == 3:
                result[key] = strings[value]
            elif kind == 0x12:
                result[key] = bool(value)
            elif kind in (0x10, 0x11):
                result[key] = value
            elif raw != NO:
                result[key] = strings[raw]
            else:
                result[key] = f'@0x{value:08x}'
        return result
    summary = {'permissions': [], 'providers': [], 'launchers': []}
    stack = []
    component = None
    application_label = None
    for chunk in chunks:
        kind = U16(chunk, 0)
        if kind == 0x102:
            tag = strings[U32(chunk, 20)]
            attrs = attributes(chunk)
            stack.append(tag)
            if tag == 'manifest':
                for key in ['package', 'versionCode', 'versionName']:
                    summary[key] = attrs.get(key)
            elif tag == 'uses-sdk':
                summary['minSdkVersion'] = attrs.get('minSdkVersion')
                summary['targetSdkVersion'] = attrs.get('targetSdkVersion')
            elif tag.startswith('uses-permission'):
                summary['permissions'].append(attrs.get('name'))
            elif tag == 'application':
                application_label = attrs.get('label')
                summary['label'] = application_label
            elif tag in ('activity', 'activity-alias'):
                component = dict(attrs)
                component['actions'], component['categories'] = [], []
            elif tag == 'action' and component is not None:
                component['actions'].append(attrs.get('name'))
            elif tag == 'category' and component is not None:
                component['categories'].append(attrs.get('name'))
            elif tag == 'provider' and 'application' in stack:
                summary['providers'].append(attrs)
        elif kind == 0x103:
            tag = strings[U32(chunk, 20)]
            if tag in ('activity', 'activity-alias') and component is not None:
                if ('android.intent.action.MAIN' in component['actions'] and
                        'android.intent.category.LAUNCHER' in component['categories']):
                    summary['launchers'].append({'name': component.get('name'),
                        'label': component.get('label', application_label)})
                component = None
            if stack:
                stack.pop()
    return summary
