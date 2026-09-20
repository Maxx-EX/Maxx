# Maxx Stage1: 最小可执行程序（纯机器码）
# boot0 加载并跳转到这里
# 构建：as --64 stage1.s -o stage1.o && ld -o maxxc-stage1 stage1.o -e _start

.global _start
.text

.equ SYS_WRITE,  1
.equ SYS_EXIT,   60

_start:
    # 打印 "Hello from Maxx Stage1 (machine code)"
    lea     msg(%rip), %rdi
    call    print

    # 打印版本号
    lea     ver(%rip), %rdi
    call    print

    # 打印提示
    lea     hint(%rip), %rdi
    call    print

    # 退出
    mov     $SYS_EXIT, %rax
    xor     %rdi, %rdi
    syscall

# print(rdi = string)
print:
    push    %rsi
    push    %rdx
    mov     %rdi, %rsi
    xor     %rdx, %rdx
.len:
    cmpb    $0, (%rsi,%rdx)
    je      .done
    inc     %rdx
    jmp     .len
.done:
    mov     $SYS_WRITE, %rax
    mov     $1, %rdi
    syscall
    pop     %rdx
    pop     %rsi
    ret

.data
msg:
    .ascii  "\n========================================\n"
    .ascii  "Hello from Maxx Stage1!\n"
    .ascii  "This program runs directly from machine code.\n"
    .ascii  "No Python. No C. No libc. No mainstream language.\n"
    .ascii  "========================================\n\n"
    .byte   0

ver:
    .ascii  "Maxx Compiler v0.1-stage1 (machine code bootstrap)\n"
    .byte   0

hint:
    .ascii  "This is the first hand-written stage.\n"
    .ascii  "Next: Maxx will compile itself (Level 2 self-hosting).\n\n"
    .byte   0
