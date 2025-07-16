Imports Microsoft.AspNetCore.Mvc

Public Class S5146DotnetNoncompliant
    Inherits Controller

    <HttpGet>
    Public Sub Redirect(Url As String)
        Response.Redirect(Url)
    End Sub
End Class
