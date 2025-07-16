Imports Microsoft.AspNetCore.Mvc
Imports System.Diagnostics

Public Class S5883DotnetCompliant
    Inherits Controller

    Public Sub Run(Args As String)
        Dim P As New Process()
        P.StartInfo.FileName = "/usr/bin/find"
        P.StartInfo.ArgumentList.Add("/some/folder")
        P.StartInfo.ArgumentList.Add("-iname")
        P.StartInfo.ArgumentList.Add(Args)
        P.Start()
    End Sub
End Class
