import yaml
import os
from collections import OrderedDict
from utils.data_utils import TaskType, MetricType, ModelType, LossType

class TasksParam:
    '''
    This class keeps the details mentioned in the tasks yml file as attributes.
    '''
    def __init__(self, taskFilePath):
        # dictioanry holding all the tasks details with 
        # task name as key.
        self.taskDetails = yaml.safe_load(open(taskFilePath))
        self.modelType = self.validity_checks()

        classNumMap = {}
        taskTypeMap = {}
        taskNameIdMap = {}
        taskIdNameMap = OrderedDict()
        metricsMap = {}
        dropoutProbMap = {}
        lossMap = {}
        labelMap = {}
        lossWeightMap = {}
        fileNamesMap = {}

        for i, (taskName, taskVals) in enumerate(self.taskDetails.items()):
            classNumMap[taskName] = taskVals["class_num"]
            taskNameIdMap[taskName] = i
            taskIdNameMap[i] = taskName
            taskTypeMap[taskName] = TaskType[taskVals["task_type"]]
            metricsMap[taskName] = tuple(MetricType[metric_name] for metric_name in taskVals["metrics"])
            fileNamesMap[taskName] = list(taskVals["file_names"])

            modelConfig = None
            dropoutProbMap[taskName] = 0.05
            lossMap[taskName] = None
            lossWeightMap[taskName] = float(1.0)
            labelMap[taskName] = None

            if "config_name" in taskVals:
                modelConfig = taskVals["config_name"]

            if "dropout_prob" in taskVals:
                dropoutProbMap[taskName] = taskVals["dropout_prob"]

            # loss map
            if "loss_type" in taskVals:
                lossMap[taskName] = LossType[taskVals["loss_type"]]

            if "label_map" in taskVals:
                '''
                Label Map is the list of label names (or tag names in NER) which are
                present in the data. We make it into dict. This dict will be used to create the label to index
                map and hence is important to maintain order. It is required in case of 
                NER. For classification tasks, if the labels are already numeric in data,
                label map is not required, but if not, then required.

                DO NOT ADD ANY EXTRA SPECIAL TOKEN LIKE ['CLS'], 'X', ['SEP'] IN LABEL MAP OR COUNT IN CLASS NUMBER
                '''
                labelMap[taskName] = {lab:i for i, lab in enumerate(taskVals["label_map"])}
                #print(len(labelMap[taskName]))
                #print(classNumMap[taskName])
                assert len(labelMap[taskName]) == classNumMap[taskName], "entries in label map doesn't match with class number"

            if "loss_weight" in taskVals:
                '''
                loss weight for individual task. This factor 
                will be multiplied directly to the loss calculated
                for backpropagation
                '''
                lossWeightMap[taskName] = float(taskVals["loss_weight"])
            else:
                lossWeightMap[taskName] = float(1.0)

        self.classNumMap = classNumMap
        self.taskTypeMap = taskTypeMap
        self.taskNameIdMap = taskNameIdMap
        self.taskIdNameMap = taskIdNameMap
        self.modelConfig = modelConfig
        self.metricsMap = metricsMap
        self.fileNamesMap = fileNamesMap
        self.dropoutProbMap = dropoutProbMap
        self.lossMap = lossMap
        self.labelMap =labelMap
        self.lossWeightMap = lossWeightMap

    def validity_checks(self):
        '''
        Check if the yml has correct form or not.
        '''
        requiredParams = {"class_num", "task_type", "metrics", "loss_type", "file_names"}
        uniqueModel = set()
        uniqueConfig = set()
        for taskName, taskVals in self.taskDetails.items():
            # check task name
            assert taskName.isalpha(), "only alphabets are allowed in task name. No special chracters/numbers/whitespaces allowed. Task Name: %s" % taskName

            # check all required arguments
            assert len(requiredParams.intersection(set(taskVals.keys()))) == len(requiredParams), "following parameters are required {}".format(requiredParams)

            #check is loss, metric. model type is correct
            try:
                LossType[taskVals["loss_type"]]
                ModelType[taskVals["model_type"]]
                [MetricType[m] for m in taskVals["metrics"]]
            except:
                print("allowed loss {}".format(list(LossType)))
                print("allowed model type {}".format(list( ModelType)))
                print("allowed metric type {}".format(list(MetricType)))
                raise

            # check model type, only one model type is allowed for all tasks
            uniqueModel.add(ModelType[taskVals["model_type"]])
            if "config_name" in taskVals:
                uniqueConfig.add(taskVals["config_name"])

            #check if all data files exists for task
            #for fileName in taskVals['file_names']:
                #assert os.path.exists(fileName)
            
            # we definitely require label mapping for NER task
            if taskVals["task_type"] == 'NER':
                assert "label_map" in taskVals, "Unique Tags/Labels needs to be mentioned in label_map for NER"

        assert len(uniqueModel) == 1, "Only one type of model can be shared across all tasks"
        assert len(uniqueConfig) <= 1, "Model config has to be same across all shared tasks"

        #return model type from here
        return list(uniqueModel)[0]


