Imports Microsoft.AspNetCore.Mvc

Public Class S5146DotnetCompliant
    Inherits Controller

    Private ReadOnly AllowedUrls() As String = {"/", "/login", "/logout"}

    <HttpGet>
    Public Sub Redirect(Url As String)
        If AllowedUrls.Contains(Url) Then
            Response.Redirect(Url)
        End If
    End Sub
End Class
