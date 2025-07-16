Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.AspNetCore.Http

Public Class S5131AspNetNoncompliant
    Inherits Controller

    <HttpGet>
    Public Sub Hello(Name As String, Response As HttpResponse)
        Dim Html As String = "<h1>Hello" + Name + "</h1>"
        Response.WriteAsync(Html)
    End Sub
End Class
