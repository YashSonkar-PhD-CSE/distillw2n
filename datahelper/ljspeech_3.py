# Adopted from torchaudio.datasets.LJSPEECH
import csv
import os
from pathlib import Path
from typing import Tuple, Union

import torchaudio
from torch import Tensor
from torch.utils.data import Dataset
from torchaudio._internal import download_url_to_file
# from torchaudio.datasets.utils import _extract_tar
import torch

_RELEASE_CONFIGS = {
    "release1": {
        "folder_in_archive": "wavs",
        "url": "https://data.keithito.com/data/speech/LJSpeech-1.1.tar.bz2",
        "checksum": "be1a30453f28eb8dd26af4101ae40cbf2c50413b1bb21936cbcdc6fae3de8aa5",
    }
}


class LJSPEECH(Dataset):
    """*LJSpeech-1.1* :cite:`ljspeech17` dataset.

    Args:
        root (str or Path): Path to the directory where the dataset is found or downloaded.
        url (str, optional): The URL to download the dataset from.
            (default: ``"https://data.keithito.com/data/speech/LJSpeech-1.1.tar.bz2"``)
        folder_in_archive (str, optional):
            The top-level directory of the dataset. (default: ``"wavs"``)
        download (bool, optional):
            Whether to download the dataset if it is not found at root path. (default: ``False``).
    """

    def __init__(
        self,
        root: Union[str, Path],
        url: str = _RELEASE_CONFIGS["release1"]["url"],
        folder_in_archive: str = _RELEASE_CONFIGS["release1"]["folder_in_archive"],
        download: bool = False,
        process_type_1: str="pseudo",
        process_type_2: str="se-vad",
    ) -> None:

        self._parse_filesystem(root, url, folder_in_archive, download, process_type_1, process_type_2)

    def _parse_filesystem(self, root: str, url: str, folder_in_archive: str, 
                          download: bool, process_type_1: str, process_type_2: str) -> None:
        root = Path(root)

        basename = os.path.basename(url)
        archive = root / basename

        basename = Path(basename.split(".tar.bz2")[0])
        folder_in_archive = basename / folder_in_archive

        self._path = root / folder_in_archive
        self._metadata_path = root / basename / "metadata.csv"
        
        self._process_type_1 = process_type_1
        self._process_type_2 = process_type_2
        '''
        if download:
            if not os.path.isdir(self._path):
                if not os.path.isfile(archive):
                    checksum = _RELEASE_CONFIGS["release1"]["checksum"]
                    download_url_to_file(url, archive, hash_prefix=checksum)
                _extract_tar(archive)
        else:
            if not os.path.exists(self._path):
                raise RuntimeError(
                    f"The path {self._path} doesn't exist. "
                    "Please check the ``root`` path or set `download=True` to download it"
                )
        '''
        with open(self._metadata_path, "r", newline="", encoding='utf-8') as metadata:
            flist = csv.reader(metadata, delimiter="|", quoting=csv.QUOTE_NONE)
            self._flist = list(flist)

    def __getitem__(self, n: int) -> Tuple[Tensor, int, str, str]:
        """Load the n-th sample from the dataset.

        Args:
            n (int): The index of the sample to be loaded

        Returns:
            Tuple of the following items;

            Tensor:
                Waveform
            int:
                Sample rate
            str:
                Transcript
            str:
                Normalized Transcript
        """
        line = self._flist[n]
        fileid, transcript, normalized_transcript = line
        fileid_audio_o = self._path / (fileid + ".wav")
        # fileid_audio = Path(str(fileid_audio_o).replace('LJSpeech-1.1', "LJSpeech-1.1-{}".format("ppw")))
        fileid_audio = fileid_audio_o
        waveform, sample_rate = torchaudio.load(fileid_audio)
        fileid_audio = Path(str(fileid_audio_o).replace('LJSpeech-1.1', "LJSpeech-1.1-{}".format(self._process_type_1)))
        waveform_pseudo, sample_rate = torchaudio.load(fileid_audio)
        fileid_audio = Path(str(fileid_audio_o).replace('LJSpeech-1.1', "LJSpeech-1.1-{}".format(self._process_type_2)))
        waveform_vad, sample_rate = torchaudio.load(fileid_audio)
        return (
            waveform,
            waveform_pseudo,
            waveform_vad,
            sample_rate,
            transcript,
            normalized_transcript,
        )

    def __len__(self) -> int:
        return len(self._flist)
