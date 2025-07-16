Imports Microsoft.AspNetCore.Mvc

<ApiController>
<Route("Example")>
Public Class S6549AspNetNoncompliant
    Inherits ControllerBase

    Private Const TargetDirectory As String = "/path/to/target/directory"

    Public Function FileExists() As IActionResult
        Dim File As String = Request.Query("file")
        Dim Path As String = TargetDirectory & File
        If Not System.IO.File.Exists(Path) Then ' Noncompliant
            Return NotFound("File not found")
        End If
        Return Ok("File found")
    End Function
End Class
