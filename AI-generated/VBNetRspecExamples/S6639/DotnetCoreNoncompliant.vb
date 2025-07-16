Imports System.Collections
Imports Microsoft.AspNetCore.Mvc

Public Class S6639DotnetCoreNoncompliant
    Inherits Controller

    <Route("NonCompliantArrayList")>
    Public Function NonCompliantArrayList() As String
        Dim Size As Integer
        Try
            Size = Integer.Parse(Request.Query("size"))
        Catch ex As FormatException
            Return "Number format exception while reading size"
        End Try
        Dim ArrayList As New ArrayList(Size) ' Noncompliant
        Return Size.ToString() & " bytes were allocated."
    End Function
End Class
