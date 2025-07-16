Imports System.Collections
Imports Microsoft.AspNetCore.Mvc

Public Class S6639DotnetCoreCompliant
    Inherits Controller

    Public Const MaxAllocSize As Integer = 1024

    <Route("CompliantArrayList")>
    Public Function CompliantArrayList() As String
        Dim Size As Integer
        Try
            Size = Integer.Parse(Request.Query("size"))
        Catch ex As FormatException
            Return "Number format exception while reading size"
        End Try
        Size = Math.Min(Size, MaxAllocSize)
        Dim ArrayList As New ArrayList(Size)
        Return Size.ToString() & " bytes were allocated."
    End Function
End Class
