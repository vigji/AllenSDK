import os
import pandas as pd

from allensdk.brain_observatory.behavior.behavior_ophys_api.behavior_ophys_nwb_api import BehaviorOphysNwbApi
from allensdk.brain_observatory.behavior.behavior_ophys_session import BehaviorOphysSession
from allensdk.core.lazy_property import LazyProperty

csv_io = {
    'reader': lambda path: pd.read_csv(path, index_col='Unnamed: 0'),
    'writer': lambda path, df: df.to_csv(path)
}

cache_json_example = {'manifest_path': '/allen/programs/braintv/workgroups/nc-ophys/visual_behavior/SWDB_2019/visual_behavior_data_manifest.csv',
                      'nwb_base_dir': '/allen/programs/braintv/workgroups/nc-ophys/visual_behavior/SWDB_2019/nwb_files',
                      'analysis_files_base_dir': '/allen/programs/braintv/workgroups/nc-ophys/visual_behavior/SWDB_2019/analysis_files'
                      }

class BehaviorProjectCache(object):

    def __init__(self, cache_json):
        self.manifest = csv_io['reader'](cache_json['manifest_path'])
        self.nwb_base_dir = cache_json['nwb_base_dir']
        self.analysis_files_base_dir = cache_json['analysis_files_base_dir']

    def get_nwb_filepath(self, experiment_id):
        return os.path.join(self.nwb_base_dir, 'behavior_ophys_session_{}.nwb'.format(experiment_id))

    def get_trial_response_df_path(self, experiment_id):
        return os.path.join(self.analysis_files_base_dir, 'trial_response_df_{}.h5'.format(experiment_id))

    def get_flash_response_df_path(self, experiment_id):
        return os.path.join(self.analysis_files_base_dir, 'flash_response_df_{}.h5'.format(experiment_id))

    def get_extended_stumulus_presentations_df(self, experiment_id):
        return os.path.join(self.analysis_files_base_dir, 'extended_stimulus_presentations_df_{}.h5'.format(experiment_id))

    def get_session(self, experiment_id):
        nwb_path = self.get_nwb_filepath(experiment_id)
        trial_response_df_path = self.get_trial_response_df_path(experiment_id)
        flash_response_df_path = self.get_flash_response_df_path(experiment_id)
        extended_stim_df_path = self.get_extended_stumulus_presentations_df(experiment_id)
        api = ExtendedNwbApi(nwb_path, trial_response_df_path, flash_response_df_path, extended_stim_df_path)
        session = ExtendedBehaviorSession(api)
        return session 

    def get_container_sessions(self, container_id):
        # TODO: Instead return a dict with stage name as key
        container_manifest = self.manifest.groupby('container_id').get_group(container_id)
        return [self.get_session(experiment_id) for experiment_id in container_manifest['ophys_experiment_id'].values]


class ExtendedNwbApi(BehaviorOphysNwbApi):
    
    def __init__(self, nwb_path, trial_response_df_path, flash_response_df_path, extended_stimulus_presentations_df_path):
        super(ExtendedNwbApi, self).__init__(path=nwb_path, filter_invalid_rois=True)
        self.trial_response_df_path = trial_response_df_path
        self.flash_response_df_path = flash_response_df_path
        self.extended_stimulus_presentations_df_path = extended_stimulus_presentations_df_path

    def get_trial_response_df(self):
        return pd.read_hdf(self.trial_response_df_path, key='df')

    def get_flash_response_df(self):
        return pd.read_hdf(self.flash_response_df_path, key='df')

    def get_extended_stumulus_presentations_df(self):
        return pd.read_hdf(self.extended_stimulus_presentations_df_path, key='df')

    def get_stimulus_presentations(self):
        stimulus_presentations = super(ExtendedNwbApi, self).get_stimulus_presentations()
        extended_stimulus_presentations = self.get_extended_stumulus_presentations_df()
        extended_stimulus_presentations = extended_stimulus_presentations.drop(columns = ['omitted'])
        return stimulus_presentations.join(extended_stimulus_presentations)


class ExtendedBehaviorSession(BehaviorOphysSession):

    def __init__(self, api):

        super(ExtendedBehaviorSession, self).__init__(api)
        self.api = api

        self.trial_response_df = LazyProperty(self.get_trial_response_df)
        self.flash_response_df = LazyProperty(self.api.get_flash_response_df)
        #  self.stimulus_presentations = LazyProperty(self.get_stimulus_presentations)
        self.image_index = LazyProperty(self.get_stimulus_index)

    def get_trial_response_df(self):
        trial_response_df = self.api.get_trial_response_df()
        trials_copy = self.trials.copy()

        #TODO: Can we make this not mess with the trials index?
        trials_copy.index.names = ['trial_id']
        trial_response_df = trial_response_df.join(trials_copy)
        return trial_response_df

    #  def get_stimulus_presentations(self):
    #      stimulus_presentations = self.api.get_stimulus_presentations()
    #      extended_stimulus_presentations = self.api.get_extended_stumulus_presentations_df()
    #      return stimulus_presentations.join(extended_stimulus_presentations)

    def get_stimulus_index(self):
        return self.stimulus_presentations.groupby('image_index').apply(lambda group: group['image_name'].unique()[0])
