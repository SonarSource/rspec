Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.AspNetCore.Http
Imports System.Text.Json

Public Class S5135DotnetCompliant
    Inherits Controller

    <HttpPost>
    Public Function Deserialize(InputFile As IFormFile) As ActionResult
        Dim ExpectedObject As ExpectedType = CType(JsonSerializer.Deserialize(Of ExpectedType)(InputFile.OpenReadStream()), ExpectedType)
    End Function
End Class
