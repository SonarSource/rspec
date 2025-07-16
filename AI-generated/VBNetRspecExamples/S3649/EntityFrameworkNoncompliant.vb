Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.EntityFrameworkCore

Public Class S3649EntityFrameworkNoncompliant
    Inherits Controller

    Private ReadOnly Context As DbContext

    Public Function Authenticate(User As String, Pass As String) As IActionResult
        Dim Query As String = "SELECT COUNT(*) FROM users WHERE user = '" & User & "' AND pass = '" & Pass & "'"

        Dim QueryResults = Context.Database.FromSqlRaw(Query)

        If QueryResults = 0 Then
            Return Unauthorized()
        End If

        Return Ok()
    End Function
End Class
