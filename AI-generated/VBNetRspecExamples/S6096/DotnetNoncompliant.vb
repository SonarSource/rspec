Imports System.IO
Imports System.IO.Compression
Imports System.Collections.Generic
Imports Microsoft.AspNetCore.Mvc

Public Class S6096DotnetNoncompliant
    Inherits Controller

    Private Shared TargetDirectory As String = "/example/directory/"

    Public Sub ExtractEntry(EntriesEnumerator As IEnumerator(Of ZipArchiveEntry))
        Dim Entry As ZipArchiveEntry = EntriesEnumerator.Current
        Dim DestinationPath As String = Path.Combine(TargetDirectory, Entry.FullName)

        Entry.ExtractToFile(DestinationPath)
    End Sub
End Class
