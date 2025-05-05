# mini_backend.py

import re

def parse_allocas(ir_lines):
    offsets = {}
    offset = -8
    for line in ir_lines:
        m = re.match(r'\s*%\"?([\w\.]+)\"? = alloca i32', line)
        if m:
            var = m.group(1)
            offsets[var] = offset
            offset -= 8
    return offsets

def ir_to_asm(ir_lines, var_offsets):
    asm = []
    asm.append("section .text")
    asm.append("global main")
    
    current_func = None

    for line in ir_lines:
        line = line.rstrip()
        
        # Skip target lines
        if line.startswith("target") or line.startswith(";"):
            continue

        # Function start: define i32 @"foo"(...)
        m = re.match(r'\s*define i32 @"?([\w_]+)"?\(.*\)\s*{', line)
        if m:
            func = m.group(1)
            current_func = func
            asm.append(f"\n{func}:")
            # prologue
            asm += [
                "    push    rbp",
                "    mov     rbp, rsp",
                f"    sub     rsp, {-min(var_offsets.values(), default=0)}"
            ]
            continue

        # Function end: }
        if line.strip() == "}":
            # epilogue
            asm += [
                "    leave",
                "    ret"
            ]
            current_func = None
            continue

        # Alloca handled by parse_allocas()
        if "alloca i32" in line:
            continue

        # store immediate
        m = re.match(r'\s*store i32 (\d+), i32\* %\"?([\w\.]+)\"?', line)
        if m:
            val, var = m.groups()
            ofs = var_offsets[var]
            asm.append(f"    mov     DWORD [rbp{ofs:+}], {val}")
            continue

        # store register result (eax)
        m = re.match(r'\s*store i32 %\w+, i32\* %\"?([\w\.]+)\"?', line)
        if m:
            var = m.group(1)
            ofs = var_offsets[var]
            asm.append(f"    mov     [rbp{ofs:+}], eax")
            continue

        # load into eax
        m = re.match(r'\s*%(\w+) = load i32, i32\* %\"?([\w\.]+)\"?', line)
        if m:
            tmp, var = m.groups()
            ofs = var_offsets[var]
            asm.append(f"    mov     eax, DWORD [rbp{ofs:+}]")
            continue

        # call
        m = re.match(r'\s*%(\w+) = call i32 @"?([\w_]+)"?\((.*)\)', line)
        if m:
            _, func, args = m.groups()
            # split args: i32 %x, i32 %y
            parts = [a.strip() for a in args.split(",")]
            # assume args in order: put first in edi, second in esi
            for i, part in enumerate(parts):
                if part.startswith("i32 "):
                    reg = part.split()[1]
                    if i == 0:
                        asm.append(f"    mov     edi, DWORD [rbp{var_offsets.get(reg,0):+}]")
                    elif i == 1:
                        asm.append(f"    mov     esi, DWORD [rbp{var_offsets.get(reg,0):+}]")
            asm.append(f"    call    {func}")
            asm.append("    mov     eax, eax")
            continue

        # add
        if " = add i32 " in line:
            asm += ["    pop     rbx", "    add     eax, rbx"]
            continue

        # sub
        if " = sub i32 " in line:
            asm += ["    pop     rbx", "    sub     rbx, eax", "    mov     eax, rbx"]
            continue

        # mul
        if " = mul i32 " in line:
            asm += ["    imul    eax, ebx"]
            continue

        # sdiv
        if " = sdiv i32 " in line:
            asm += ["    cqo", "    idiv    ebx"]
            continue

        # icmp sgt
        m = re.match(r'\s*%\w+ = icmp sgt i32 %\w+, (\d+)', line)
        if m:
            val = m.group(1)
            asm += [f"    cmp     eax, {val}", "    setg    al", "    movzx   eax, al"]
            continue

        # icmp ne
        if " = icmp ne i32 " in line:
            asm += ["    cmp     eax, 0", "    setne   al", "    movzx   eax, al"]
            continue

        # conditional branch
        if line.strip().startswith("br i1"):
            asm += ["    cmp     al, 0", "    je      else", "    jmp     then"]
            continue

        # unconditional branch
        m = re.match(r'\s*br label %\"?([\w\.]+)\"?', line)
        if m:
            asm.append(f"    jmp     {m.group(1)}")
            continue

        # labels
        m = re.match(r'\s*([\w\.]+):', line)
        if m:
            asm.append(f"{m.group(1)}:")
            continue

        # return immediate
        m = re.match(r'\s*ret i32 (\d+)', line)
        if m:
            asm += ["    mov     eax, " + m.group(1), "    leave", "    ret"]
            continue

        # return register
        if "ret i32 %" in line:
            asm += ["    ; return in eax", "    leave", "    ret"]
            continue

        # everything else
        if line.strip():
            asm.append(f"    ; unhandled IR: {line}")

    return "\n".join(asm)


if __name__ == "__main__":
    with open("output.ll") as f:
        ir_lines = f.readlines()

    var_offsets = parse_allocas(ir_lines)
    asm = ir_to_asm(ir_lines, var_offsets)
    with open("output.s", "w") as out:
        out.write(asm)

    print("Generated output.s")
    print(asm)
    print("Assembly code written to output.s")