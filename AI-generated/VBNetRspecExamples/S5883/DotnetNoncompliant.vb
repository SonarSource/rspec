Imports Microsoft.AspNetCore.Mvc
Imports System.Diagnostics

Public Class S5883DotnetNoncompliant
    Inherits Controller

    Public Sub Run(Args As String)
        Dim P As New Process()
        P.StartInfo.FileName = "/usr/bin/find"
        P.StartInfo.Arguments = "/some/folder -iname " & Args
        P.Start()
    End Sub
End Class
