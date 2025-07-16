Imports Microsoft.AspNetCore.Mvc
Imports System.Diagnostics

Public Class S6350RuleNoncompliant
    Inherits Controller

    Public Sub RunFind(Input As String)
        Dim P As New Process()
        P.StartInfo.FileName = "/usr/bin/find"
        P.StartInfo.ArgumentList.Add(Input) ' Sensitive
        P.Start()
    End Sub
End Class
