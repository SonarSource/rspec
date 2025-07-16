Imports System.CodeDom.Compiler
Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.VisualBasic

Public Class S5334DotnetCompliant
    Inherits Controller

    Public Sub Run(Message As String)
        Const Code As String = "
            Imports System
            Public Class MyClass
                Public Sub MyMethod(input As String)
                    Console.WriteLine(input)
                End Sub
            End Class
        "

        Dim Provider = CodeDomProvider.CreateProvider("VisualBasic")
        Dim CompilerParameters As New CompilerParameters()
        CompilerParameters.ReferencedAssemblies.Add("System.dll")
        CompilerParameters.ReferencedAssemblies.Add("System.Runtime.dll")
        Dim CompilerResults = Provider.CompileAssemblyFromSource(CompilerParameters, Code)
        Dim MyInstance As Object = CompilerResults.CompiledAssembly.CreateInstance("MyClass")
        MyInstance.GetType().GetMethod("MyMethod").Invoke(MyInstance, New Object() {Message}) ' Pass message to dynamic method
    End Sub
End Class
