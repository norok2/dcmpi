====================================
dcmpi: DICOM Preprocessing Interface
====================================

This software implements an automated information extraction tool from DICOM
files containing MRI acquisitions. It is specifically targeted at the output
of the Siemens scanners, although it should be easily adaptable to other
vendors and eventually even different acquisition modalities.

It features a Qt-based GUI to manage the extraction locations, tasks and
the most used options. This is also mirrored by a CLI of the same software.

Additionally, several other command-line tools are provided, which offer a
much finer control over the single tasks.

The available tasks are:

- DICOM copy/moving and sorting according to acquisition
  (this includes a JSON summary of the acquisitions and series)
- extraction of DICOM metadata and experimental storing as JSON
- extraction of acquisition protocol information
- extraction of human-friendly information from the DICOM, stored as JSON
- extraction of the image data and conversion to the popular NIfTI format
  (this is supported through the software
  `dcm2nii <http://www.cabiatl.com/mricro/mricron/dcm2nii.html>`_,
  with partial support for other  programs, e.g.
  `isis <https://github.com/isis-group/isis>`_)
- creation of HTML reports from the DICOM information
  (PDF conversion is supported via `wkhtmltopdf <http://wkhtmltopdf.org>`_)
- backup of the DICOM files as compressed archives
- monitor of a folder to detect appearance of new DICOM files
