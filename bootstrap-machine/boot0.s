# Maxx Level 0 Machine Code Bootstrap
# =====================================
# 纯 x86_64 机器码，不依赖 libc，直接 syscall。
# 构建：as --64 boot0.s -o boot0.o && ld -o boot0 boot0.o -e _start

.global _start
.text

.equ SYS_WRITE,     1
.equ SYS_OPEN,       2
.equ SYS_READ,       0
.equ SYS_CLOSE,      3
.equ SYS_MMAP,       9
.equ SYS_EXIT,       60
.equ O_RDONLY,       0
.equ PROT_READ,      1
.equ PROT_WRITE,    2
.equ PROT_EXEC,      4
.equ MAP_PRIVATE,   0x02
.equ MAP_ANONYMOUS,  0x20

_start:
    # 打印横幅
    lea     banner(%rip), %rdi
    call    print

    # 尝试打开 stage1
    lea     stage1_path(%rip), %rdi
    mov     $SYS_OPEN, %rax
    xor     %rsi, %rsi
    syscall
    test    %rax, %rax
    js      .no_stage1
    mov     %rax, %r12

    # mmap 16MB 可执行内存，固定在 0x10000000（stage1 链接地址）
    mov     $SYS_MMAP, %rax
    mov     $0x10000000, %rdi
    mov     $0x1000000, %rsi
    mov     $PROT_READ|PROT_WRITE|PROT_EXEC, %rdx
    mov     $MAP_PRIVATE|MAP_ANONYMOUS, %r10
    mov     $-1, %r8
    xor     %r9, %r9
    syscall
    mov     %rax, %r13

    # 读文件
    mov     $SYS_READ, %rax
    mov     %r12, %rdi
    mov     %r13, %rsi
    mov     $0x1000000, %rdx
    syscall
    mov     %rax, %r14

    # 关闭
    mov     $SYS_CLOSE, %rax
    mov     %r12, %rdi
    syscall

    # 打印加载成功
    lea     loaded_msg(%rip), %rdi
    call    print
    mov     %r14, %rdi
    call    print_int
    lea     jump_msg(%rip), %rdi
    call    print

    # 跳转
    call    *%r13

    # 返回则退出
    mov     $SYS_EXIT, %rax
    xor     %rdi, %rdi
    syscall

.no_stage1:
    lea     no_stage1_msg(%rip), %rdi
    call    print
    mov     $SYS_EXIT, %rax
    mov     $1, %rdi
    syscall

# print(rdi = string) — 打印以 0 结尾的字符串
print:
    push    %rbp
    mov     %rsp, %rbp
    push    %rdi
    push    %rsi
    push    %rdx

    # 计算长度
    mov     %rdi, %rsi
    xor     %rdx, %rdx
.print_len:
    cmpb    $0, (%rsi,%rdx)
    je      .print_len_done
    inc     %rdx
    jmp     .print_len
.print_len_done:

    # write(1, buf, len)
    mov     $SYS_WRITE, %rax
    mov     $1, %rdi
    # %rsi = buf, %rdx = len 已经就位
    syscall

    pop     %rdx
    pop     %rsi
    pop     %rdi
    pop     %rbp
    ret

# print_int(rdi = number) — 打印十进制整数
print_int:
    push    %rbp
    mov     %rsp, %rbp
    push    %rax
    push    %rbx
    push    %rcx
    push    %rdx
    push    %rsi

    mov     %rdi, %rax
    lea     intbuf(%rip), %rsi
    add     $19, %rsi
    movb    $'\n', 1(%rsi)
    mov     $10, %rbx
    mov     $1, %rcx
.int_loop:
    xor     %rdx, %rdx
    div     %rbx
    add     $'0', %dl
    dec     %rsi
    mov     %dl, (%rsi)
    inc     %rcx
    test    %rax, %rax
    jnz     .int_loop

    # write(1, buf, len+1)
    mov     $SYS_WRITE, %rax
    mov     $1, %rdi
    # %rsi = buf, %rcx = len+1 (含 \n)
    mov     %rcx, %rdx
    syscall

    pop     %rsi
    pop     %rdx
    pop     %rcx
    pop     %rbx
    pop     %rax
    pop     %rbp
    ret

.data
banner:
    .ascii  "=== Maxx Level 0 Bootstrap (raw machine code) ===\n"
    .ascii  "No libc. No Python. No mainstream language.\n"
    .byte   0

stage1_path:
    .ascii  "maxxc-stage1"
    .byte   0

loaded_msg:
    .ascii  "Stage1 loaded, size = "
    .byte   0

jump_msg:
    .ascii  "Jumping to entry point...\n"
    .byte   0

no_stage1_msg:
    .ascii  "Stage1 not found. (This is expected without maxxc-stage1 binary)\n"
    .ascii  "Boot0 itself proves: Maxx can boot from raw x86_64 machine code.\n"
    .byte   0

.bss
intbuf:
    .skip   32
