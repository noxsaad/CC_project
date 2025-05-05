  store i32 10, i32* %"x"
  store i32 20, i32* %"y"
  store i32 %"add_call", i32* %"result"
  br i1 %"ifcond", label %"then", label %"else"
  store i32 100, i32* %"z"
  store i32 %"addtmp", i32* %"result"
  store i32 %"a", i32* %"a.1"
  store i32 %"b", i32* %"b.1"
  ret i32 %"addtmp"
; ModuleID = "cc_module"
target triple = "x86_64-pc-windows-msvc-elf"
target datalayout = ""
  %"x" = alloca i32
  %"y" = alloca i32
  %"result" = alloca i32
  %"x_val" = load i32, i32* %"x"
  %"y_val" = load i32, i32* %"y"
  %"add_call" = call i32 @"add"(i32 %"x_val", i32 %"y_val")
  %"result_val" = load i32, i32* %"result"
  %"cmptmp" = icmp sgt i32 %"result_val", 25
  %"booltmp" = zext i1 %"cmptmp" to i32
  %"ifcond" = icmp ne i32 %"booltmp", 0
  %"z" = alloca i32
  %"result_val.1" = load i32, i32* %"result"
  %"z_val" = load i32, i32* %"z"
  %"addtmp" = add i32 %"result_val.1", %"z_val"
  %"a.1" = alloca i32
  %"b.1" = alloca i32
  %"a_val" = load i32, i32* %"a.1"
  %"b_val" = load i32, i32* %"b.1"
  %"addtmp" = add i32 %"a_val", %"b_val"
