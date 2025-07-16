Imports Microsoft.AspNetCore.Mvc
Imports Microsoft.AspNetCore.Http
Imports System.Runtime.Serialization.Formatters.Binary

Public Class ExpectedType
    Public Property Name As String
    Public Property Value As String
End Class

Public Class S5135DotnetNoncompliant
    Inherits Controller

    <HttpPost>
    Public Function Deserialize(InputFile As IFormFile) As ActionResult
#Disable Warning SYSLIB0011 ' BinaryFormatter is obsolete but used for demonstration
        Dim Formatter As New BinaryFormatter()
        Dim ExpectedObject As ExpectedType = CType(Formatter.Deserialize(InputFile.OpenReadStream()), ExpectedType)
    End Function
End Class
