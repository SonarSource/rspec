Imports System.Diagnostics
Imports Microsoft.AspNetCore.Mvc

Public Class S6547DotnetNoncompliant
    Inherits Controller

    Public Sub Example(Name As String, Value As String)
        Dim Proc As New Process()
        Proc.StartInfo.FileName = "path/to/executable"
        Proc.StartInfo.EnvironmentVariables.Add(Name, Value) ' Noncompliant
        Proc.Start()
    End Sub
End Class
