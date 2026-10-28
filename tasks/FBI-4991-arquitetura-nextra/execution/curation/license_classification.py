"""Classify the two verified license declarations without rewriting source bytes."""
import copy


def python_compound_license(repo, text):
    return repo == 'python/cpython' and all(marker in text for marker in [
        'PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2',
        'BEOPEN.COM LICENSE AGREEMENT FOR PYTHON 2.0',
        'CNRI LICENSE AGREEMENT FOR PYTHON 1.6.1',
        'CWI LICENSE AGREEMENT FOR PYTHON 0.9.0 THROUGH 1.2',
    ])


def scoped_license(source, license_record, root):
    result = copy.deepcopy(license_record)
    artifact = root / result.get('artifact', '__missing__')
    text = artifact.read_text() if artifact.is_file() else ''
    if python_compound_license(source.get('repo'), text):
        result['license_spdx'] = 'Python-2.0'
        result['classification_basis'] = (
            'The captured LICENSE contains the overall Python license: the PSF version 2 grant '
            'and the BeOpen, CNRI and CWI historical grants. SPDX Python-2.0 identifies that '
            'compound license; PSF-2.0 identifies only its PSF component. The selected Lib/ '
            'sources are not documentation examples covered by the separate 0BSD option.'
        )
    if (source.get('repo') == 'gitlabhq/gitlabhq' and source.get('path', '').startswith('doc/')
            and 'All content residing under the "doc/" directory' in text
            and 'CC BY-SA 4.0 license' in text):
        result['license_spdx'] = 'CC-BY-SA-4.0'
        result['classification_basis'] = (
            'The exact LICENSE line 5 assigns CC BY-SA 4.0 to doc/. This override is scoped '
            'to the selected documentation path and does not change the MIT grant for code.'
        )
        result['scope_notice_url'] = result['url'].split('#')[0] + '#L5'
    return result
