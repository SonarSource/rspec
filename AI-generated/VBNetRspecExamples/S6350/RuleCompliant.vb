Imports Microsoft.AspNetCore.Mvc
Imports System.Diagnostics

Public Class S6350RuleCompliant
    Inherits Controller

    Public Sub RunFind(Input As String)
        Dim Allowed As String() = {"-name", "-type", "-size"}
        Dim P As New Process()
        P.StartInfo.FileName = "/usr/bin/find"
        If Allowed.Contains(Input) Then
            P.StartInfo.ArgumentList.Add(Input)
        End If
        P.Start()
    End Sub
End Class
