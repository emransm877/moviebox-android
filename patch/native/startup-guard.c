/* Isolated-copy experiment: handle only the observed deliberate 0xa01 SIGBUS
 * on a non-main native thread. All other faults retain their normal handler. */
typedef unsigned long word;
struct kernel_action { void *handler; word flags; void *restorer; word mask; };
static struct kernel_action old_bus;
static struct kernel_action action;
static volatile unsigned int events;
static int installed;

__attribute__((naked)) static void restore_rt(void) {
    __asm__ volatile("mov x8, #139\nsvc #0");
}

static long call4(long number, long a, long b, long c, long d) {
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    register long x8 __asm__("x8") = number;
    __asm__ volatile("svc 0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x3), "r"(x8) : "memory", "cc");
    return x0;
}

static void bus_handler(int signal, void *info, void *context) {
    word address = *(word *)((unsigned char *)info + 16);
    long pid = call4(172, 0, 0, 0, 0);
    long tid = call4(178, 0, 0, 0, 0);
    if (signal == 7 && address == 0xa01 && pid != tid) {
        events++;
        call4(93, 0, 0, 0, 0); /* exit this specific faulting native thread */
        __builtin_unreachable();
    }
    if ((word)old_bus.handler > 1) {
        if (old_bus.flags & 4) ((void (*)(int, void *, void *))old_bus.handler)(signal, info, context);
        else ((void (*)(int))old_bus.handler)(signal);
    } else {
        call4(134, signal, (long)&old_bus, 0, 8);
        call4(131, pid, tid, signal, 0);
    }
}

__attribute__((visibility("default")))
int Java_local_popupguard_GuardProvider_installNativeGuard(void *env, void *clazz) {
    if (installed) return 0;
    action.handler = (void *)bus_handler;
    /* The observed fault clears SP, so use Android's existing alternate signal
     * stack instead of trying to deliver the handler on that invalid stack. */
    action.flags = 4 | 0x08000000 | 0x04000000; /* SIGINFO | ONSTACK | RESTORER */
    action.restorer = (void *)restore_rt;
    action.mask = 0;
    long result = call4(134, 7, (long)&action, (long)&old_bus, 8);
    if (result == 0) installed = 1;
    return (int)result;
}

__attribute__((visibility("default")))
int Java_local_popupguard_GuardProvider_nativeGuardEvents(void *env, void *clazz) {
    return (int)events;
}
