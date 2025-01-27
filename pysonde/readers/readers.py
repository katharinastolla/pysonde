"""Readers for different sounding formats
"""
import datetime as dt
import logging
import os
import sys
from functools import partial

import numpy as np

sys.path.append(os.path.dirname(__file__))
import reader_helpers as rh  # noqa: E402

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import sounding as snd  # noqa: E402


class MW41:
    """
    Reader for MW41 mwx files
    """

    def __init__(self, cfg):
        """Configure reader"""
        # Configure, which values need to be read and how they are named
        self.sync_sounding_values = cfg.level0.sync_sounding_items
        self.radiosondes_values = cfg.level0.radiosondes_sounding_items
        self.variable_name_mapping = cfg.level0.dictionary_input
        self.units = cfg.level0.input_units

    def read(self, mwx_file):
        def _get_flighttime(radio_time, start_time, launch_time):
            """
            f_flighttime = lambda radio_time: start_time + dt.timedelta(
                seconds=radio_time - np.float(launch_time)
            )
            """
            return start_time + dt.timedelta(seconds=radio_time - np.float(launch_time))

        with rh.MWX(mwx_file) as mwx:
            decompressed_files = mwx.decompressed_files

            # Get the files SynchronizedSoundingData.xml, Soundings.xml, ...
            a1, sync_filename = rh.check_availability(
                decompressed_files, "SynchronizedSoundingData.xml", True
            )
            a2, snd_filename = rh.check_availability(
                decompressed_files, "Soundings.xml", True
            )
            a3, radio_filename = rh.check_availability(
                decompressed_files, "Radiosondes.xml", True
            )
            if np.any([not a1, not a2, not a3]):
                logging.warning(
                    "No sounding data found in {}. Skipped".format(mwx_file)
                )
                return

            # Read Soundings.xml to get base time
            itemlist = rh.read_xml(snd_filename)
            for i, item in enumerate(itemlist):
                begin_time = item.attributes["BeginTime"].value
                launch_time = item.attributes["LaunchTime"].value
                station_altitude = item.attributes["Altitude"].value
            begin_time_dt = dt.datetime.strptime(begin_time, "%Y-%m-%dT%H:%M:%S.%f")

            # Read sounding data
            pd_snd = rh.get_sounding_profile(sync_filename, self.sync_sounding_values)

            # Read Radiosounding.xml to get sounding metadata
            sounding_meta_dict = rh.get_sounding_metadata(
                radio_filename, self.radiosondes_values
            )
            sounding_meta_dict["source"] = str(mwx_file)

        pd_snd = rh.rename_variables(pd_snd, self.variable_name_mapping)
        sounding_meta_dict = rh.rename_metadata(
            sounding_meta_dict, self.variable_name_mapping
        )

        # Attach units where provided
        import pandas as pd
        import pint
        import pint_pandas as pp

        ureg = pint.UnitRegistry()
        ureg.define("fraction = [] = frac")
        ureg.define("percent = 1e-2 frac = pct")
        pp.PintType.ureg = ureg
        PA_ = pp.PintArray

        pd_snd_w_units = pd.DataFrame()
        for var in pd_snd.columns:
            if var in self.units.keys():
                pd_snd_w_units[var] = PA_(pd_snd[var].values, dtype=self.units[var])
            else:
                # no units found
                pd_snd_w_units[var] = pd_snd[var].values
        pd_snd = pd_snd_w_units

        # Create flight time
        f_flighttime = partial(
            _get_flighttime, start_time=begin_time_dt, launch_time=launch_time
        )
        pd_snd["flight_time"] = pd_snd.RadioRxTimePk.apply(f_flighttime)

        # Write to class
        sounding = snd.Sounding()
        sounding.profile = pd_snd
        sounding.meta_data = sounding_meta_dict
        sounding.meta_data["launch_time"] = launch_time
        sounding.meta_data["begin_time"] = begin_time_dt
        sounding.meta_data["station_altitude"] = station_altitude
        sounding.unitregistry = ureg
        return sounding
