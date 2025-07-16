Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.EntityFrameworkCore

Public Class S3649EntityFrameworkCompliant
    Inherits Controller

    Private ReadOnly Context As DbContext

    Public Function Authenticate(User As String, Pass As String) As IActionResult
        Dim Query As String = "SELECT COUNT(*) FROM users WHERE user = {0} AND pass = {1}"

        ' Simulate parameterized query execution
        Dim QueryResults As Integer = 0

        If QueryResults = 0 Then
            Return Unauthorized()
        End If

        Return Ok()
    End Function
End Class
