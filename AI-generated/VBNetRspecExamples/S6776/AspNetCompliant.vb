Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.Extensions.Logging

<ApiController>
<Route("/")>
Public Class S6776AspNetCompliant
    Inherits ControllerBase

    Private ReadOnly Logger As ILogger(Of S6776AspNetCompliant)

    <HttpGet("Exception")>
    Public Function ExceptionEndpoint() As String
        Try
            Throw New InvalidOperationException("ExceptionMessage")
        Catch Ex As Exception
            Logger.LogError(Ex.StackTrace)
        End Try
        Return "Ok"
    End Function
End Class
