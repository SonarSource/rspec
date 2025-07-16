Imports Microsoft.AspNetCore.Mvc
Imports System.Data.SqlClient
Imports Dapper

Public Class UserEntity
    Public Property Id As Integer
    Public Property UserName As String
    Public Property Password As String
End Class

Public Class S3649DapperNoncompliant
    Inherits Controller

    Private ReadOnly ConnectionString As String

    Public Function Authenticate(User As String, Pass As String) As IActionResult
        Using Connection As New SqlConnection(ConnectionString)
            Dim Query As String = "SELECT * FROM users WHERE user = '" & User & "' AND pass = '" & Pass & "'"
            
            Dim Result = Connection.QueryFirst(Of UserEntity)(Query)
            If Result Is Nothing Then
                Unauthorized()
            End If
        End Using
        Return Ok()
    End Function
End Class
