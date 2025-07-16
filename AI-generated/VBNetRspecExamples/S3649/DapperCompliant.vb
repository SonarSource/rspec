Imports Microsoft.AspNetCore.Mvc
Imports System.Data.SqlClient
Imports Dapper

Public Class S3649DapperCompliant
    Inherits Controller

    Private ReadOnly ConnectionString As String

    Public Function Authenticate(User As String, Pass As String) As IActionResult
        Using Connection As New SqlConnection(ConnectionString)
            Dim Query As String = "SELECT * FROM users WHERE user = @UserName AND password = @Password"
            Dim Parameters = New With {.UserName = User, .Password = Pass}
            
            Dim Result = Connection.QueryFirst(Of UserEntity)(Query, Parameters)
            If Result Is Nothing Then
                Unauthorized()
            End If
        End Using
        Return Ok()
    End Function
End Class
