Imports System.Diagnostics
Imports System.Text.RegularExpressions
Imports Microsoft.AspNetCore.Mvc

Public Class S6547DotnetCompliant
    Inherits Controller

    Public Sub Example(Value As String)
        Dim Proc As New Process()
        Proc.StartInfo.FileName = "path/to/executable"
        Dim Pattern As String = "^[a-zA-Z0-9]*$"
        Dim M As Match = Regex.Match(Value, Pattern)
        If M.Success Then Proc.StartInfo.EnvironmentVariables.Add("ENV_VAR", Value)
        Proc.Start()
    End Sub
End Class
