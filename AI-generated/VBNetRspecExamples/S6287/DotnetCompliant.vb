Imports System.Web
Imports Microsoft.AspNetCore.Mvc

Public Class S6287DotnetCompliant
    Inherits Controller

    <HttpGet>
    Public Function CheckCookie() As IActionResult
        If Request.Cookies("ASP.NET_SessionId") Is Nothing Then
            Return View("GetCookie")
        End If

        Return View("Welcome")
    End Function
End Class
