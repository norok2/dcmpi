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

The subsequent data analysis is probably best performed using
`PyMRT <https://pypi.python.org/pypi/pymrt>`_, which natively understands the
output of DCMPI.

Notes
-----
This work is based on reverse engineering of the DICOM files and as such should
not be used as a reliable source of information.
Some of the most interesting features are only partially supported.
Please get in contact if you would like suggest feature requests.

WARNING
-------
This is a research tool and it is provided 'as is'.
DO **NOT** BASE ANY DIAGNOSIS ON THE INFORMATION PROCESSED BY THIS SOFTWARE!

Installation
------------
The recommended way of installing the software is through
`PyPI <https://pypi.python.org/pypi/dcmpi>`_:

.. code:: shell

    $ pip install dcmpi

Alternatively, you can the clone the source repository from
`Bitbucket <https://bitbucket.org/norok2/dcmpi>`_:

.. code:: shell

    $ mkdir dcmpi
    $ cd dcmpi
    $ git clone git@bitbucket.org:norok2/dcmpi.git
    $ python setup.py install

For more details see also ``INSTALL.rst``.

License
-------
This work is licensed through the terms and conditions of the
`GPLv3+ <http://www.gnu.org/licenses/gpl-3.0.html>`_
The use of this software for scientific purpose leading to a publication
should be acknowledged through citation of the upcoming paper.

Acknowledgements
----------------
This software originated as part of my Ph.D. work at the
`Max Planck Institute for Human Cognitive and Brain Sciences
<http://www.cbs.mpg.de>`_ and the `University of Leipzig
<http://www.uni-leipzig.de>`_.

For a complete list of authors please see ``AUTHORS.rst``.

People who have influenced this work are acknowledged in ``THANKS.rst``.

This work was partly funded by the European Union
through the Seventh Framework Programme Marie Curie Actions
via the "Ultra-High Field Magnetic Resonance Imaging: HiMR"
Initial Training Network (FP7-PEOPLE-2012-ITN-316716).
