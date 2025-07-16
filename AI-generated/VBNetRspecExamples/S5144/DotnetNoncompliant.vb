Imports Microsoft.AspNetCore.Mvc
Imports System.IO
Imports System.Net.Http
Imports System.Text.Json
Imports System.Threading.Tasks

Public Class ExampleImage
    Public Property Url As String
    Public Property Description As String
End Class

Public Class S5144DotnetNoncompliant
    Inherits Controller

    Private ReadOnly Client As New HttpClient()

    <HttpGet>
    Public Async Function ImageFetch(Location As String) As Task(Of IActionResult)
        Using Stream As Stream = Await Client.GetStreamAsync(Location) ' Noncompliant
            Dim ExampleImage As ExampleImage = Await JsonSerializer.DeserializeAsync(Of ExampleImage)(Stream)

            Return Ok(If(ExampleImage, New ExampleImage()))
        End Using
    End Function
End Class
