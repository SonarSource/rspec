Imports System.CodeDom.Compiler
Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.VisualBasic

Public Class S5334DotnetNoncompliant
    Inherits Controller

    Public Sub Run(Message As String)
        Dim Code As String = "
            Imports System
            Public Class MyClass
                Public Sub MyMethod()
                    Console.WriteLine(""" + Message + """)
                End Sub
            End Class
        "

        Dim Provider = CodeDomProvider.CreateProvider("VisualBasic")
        Dim CompilerParameters As New CompilerParameters()
        CompilerParameters.ReferencedAssemblies.Add("System.dll")
        CompilerParameters.ReferencedAssemblies.Add("System.Runtime.dll")
        Dim CompilerResults = Provider.CompileAssemblyFromSource(CompilerParameters, Code) ' Noncompliant

        Dim MyInstance As Object = CompilerResults.CompiledAssembly.CreateInstance("MyClass")
        MyInstance.GetType().GetMethod("MyMethod").Invoke(MyInstance, New Object() {})
    End Sub
End Class
