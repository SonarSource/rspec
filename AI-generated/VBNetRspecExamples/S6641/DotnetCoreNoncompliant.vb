Imports System.Data.SqlClient
Imports Microsoft.AspNetCore.Http
Imports Microsoft.AspNetCore.Mvc

Public Class S6641DotnetCoreNoncompliant
    Inherits Controller

    Public Property ConnectionString As String = "Server=10.0.0.101;Database=CustomerData"

    Public Function ConnectToDatabase(Request As HttpRequest) As SqlConnection
        Dim ConnectionStringFormatted As String = String.Format("{0};User ID={1};Password={2}",
            Me.ConnectionString,
            Request.Form("username"),
            Request.Form("password"))

        Dim Connection As New SqlConnection()
        Connection.ConnectionString = ConnectionStringFormatted ' Noncompliant
        Connection.Open()
        Return Connection
    End Function
End Class
