Imports Microsoft.AspNetCore.Mvc
Imports System.IO

<ApiController>
<Route("Example")>
Public Class S6549AspNetCompliant
    Inherits ControllerBase

    Private Const TargetDirectory As String = "/path/to/target/directory"

    Public Function FileExists() As IActionResult
        Dim File As String = Request.Query("file")
        Dim CanonicalPath As String = Path.GetFullPath(TargetDirectory & File)
        If Not CanonicalPath.StartsWith(TargetDirectory) Then
            Return NotFound("Entry is outside of the target directory")
        ElseIf Not System.IO.File.Exists(CanonicalPath) Then
            Return NotFound("File not found")
        End If
        Return Ok("File found")
    End Function
End Class
