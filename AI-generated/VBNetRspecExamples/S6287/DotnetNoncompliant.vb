Imports System.Web
Imports Microsoft.AspNetCore.Mvc

Public Class S6287DotnetNoncompliant
    Inherits Controller

    <HttpGet>
    Public Function CheckCookie(Cookie As String) As IActionResult
        If Request.Cookies("ASP.NET_SessionId") Is Nothing Then
            Response.Cookies.Append("ASP.NET_SessionId", Cookie)
        End If

        Return View("Welcome")
    End Function
End Class
