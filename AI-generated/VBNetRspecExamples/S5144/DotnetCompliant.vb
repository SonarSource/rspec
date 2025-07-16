Imports Microsoft.AspNetCore.Mvc
Imports System.IO
Imports System.Net.Http
Imports System.Text.Json
Imports System.Threading.Tasks

Public Class S5144DotnetCompliant
    Inherits Controller

    Private ReadOnly Client As New HttpClient()
    Private ReadOnly AllowedSchemes() As String = {"https"}
    Private ReadOnly AllowedDomains() As String = {"trusted1.example.com", "trusted2.example.com"}

    <HttpGet>
    Public Async Function ImageFetch(Location As String) As Task(Of IActionResult)
        Dim Uri As New Uri(Location)

        If Not AllowedDomains.Contains(Uri.Host) AndAlso Not AllowedSchemes.Contains(Uri.Scheme) Then
            Return BadRequest()
        End If

        Using Stream As Stream = Await Client.GetStreamAsync(Location)
            Dim ExampleImage As ExampleImage = Await JsonSerializer.DeserializeAsync(Of ExampleImage)(Stream)

            Return Ok(If(ExampleImage, New ExampleImage()))
        End Using
    End Function
End Class
