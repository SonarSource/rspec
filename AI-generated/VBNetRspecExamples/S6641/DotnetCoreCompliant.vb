Imports System.Data.SqlClient
Imports Microsoft.AspNetCore.Http
Imports Microsoft.AspNetCore.Mvc

Public Class S6641DotnetCoreCompliant
    Inherits Controller

    Public Property ConnectionString As String = "Server=10.0.0.101;Database=CustomerData"

    Public Function ConnectToDatabase(Request As HttpRequest) As SqlConnection
        Dim Builder As New SqlConnectionStringBuilder(ConnectionString)
        Builder.UserID = Request.Form("username")
        Builder.Password = Request.Form("password")

        Dim Connection As New SqlConnection()
        Connection.ConnectionString = Builder.ConnectionString
        Connection.Open()
        Return Connection
    End Function
End Class
