# EASY-CIM: Extracting Attributes in a Simple DictionarY of CIM data

![GitHub Tag](https://img.shields.io/github/v/tag/PNNL-CIM-Tools/EASY-CIM)
![GitHub Release Date](https://img.shields.io/github/release-date-pre/PNNL-CIM-Tools/EASY-CIM)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/PNNL-CIM-Tools/CIM-Graph/dev-pre-release.yml)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/PNNL-CIM-Tools/EASY-CIM/total?label=git%20downloads)
<!-- ![Libraries.io dependency status for GitHub repo](https://img.shields.io/librariesio/github/PNNL-CIM-Tools/EASY-CIM) -->


![PyPI - Version](https://img.shields.io/pypi/v/easycim)
![PyPI - Downloads](https://img.shields.io/pypi/dm/easycim?label=pypi%20downloads)
![PyPI - Format](https://img.shields.io/pypi/format/easycim)


![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/PNNL-CIM-Tools/EASY-CIM)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-pr/PNNL-CIM-Tools/EASY-CIM)
![GitHub commit activity](https://img.shields.io/github/commit-activity/t/PNNL-CIM-Tools/EASY-CIM)

![GitHub License](https://img.shields.io/github/license/PNNL-CIM-Tools/EASY-CIM)
<!-- ![https://doi.org/10.11578/dc.20240507.3](https://img.shields.io/badge/doi-10.11578/dc.20240507.3-blue) -->

EASY-CIM is a python library for extracting CIM data into a reduced profile with linked mRIDs listed as dictionaries of key-value pairs.

The syntax is equivalent to that of CIMantic Graphs calls with object references replaced with dictionary keys.

CIM-Graph Call:

```python
phase = network.graph[cim.ACLineSegment][UUID("rdf-id-string")].ACLineSegmentPhases[0].phase
print(phase)
```
```plaintext
cim.SinglePhaseKind.A
```

EASY-CIM Call:

```python
phase = line_data["rdf-id-string"]["ACLineSegmentPhases"][0]["phase"]
print(phase)
```
```plaintext
"A"
```


## Attribution and Disclaimer:

This software was created under a project sponsored by the U.S. Department of Energy, an agency of the United States Government.  Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any of their employees, nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe privately owned rights.

Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.


<div align="center">

PACIFIC NORTHWEST NATIONAL LABORATORY

*operated by*

BATTELLE

*for the*

UNITED STATES DEPARTMENT OF ENERGY

*under Contract DE-AC05-76RL01830*

</div>
