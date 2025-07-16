Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.AspNetCore.Http
Imports System.Net

Public Class S5131AspNetCompliant
    Inherits Controller

    <HttpGet>
    Public Sub Hello(Name As String, Response As HttpResponse)
        Dim Html As String = "<h1>Hello" + WebUtility.HtmlEncode(Name) + "</h1>"
        Response.WriteAsync(Html)
    End Sub
End Class
