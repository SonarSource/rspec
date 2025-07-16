Imports Microsoft.AspNetCore.Mvc

<ApiController>
<Route("/")>
Public Class S6776AspNetNoncompliant
    Inherits ControllerBase

    <HttpGet("Exception")>
    Public Function ExceptionEndpoint() As String
        Try
            Throw New InvalidOperationException("ExceptionMessage")
        Catch ex As Exception
            Return ex.StackTrace ' Noncompliant
        End Try
        Return "Ok"
    End Function
End Class
