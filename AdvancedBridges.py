#------------------------------------------------------------------------------------------------------------------------------------
#
# Cura AdvancedBridges Script
# Author:   btxdev
# Date:     Febrary 20, 2023
#
# Description:  postprocessing script to add the pauses before the each bridge and set infill speed
#
#------------------------------------------------------------------------------------------------------------------------------------

from ..Script import Script
from UM.Logger import Logger
from UM.Application import Application
import re

__version__ = '2.1'

def is_begin_bridge(line: str) -> bool:
    return line.startswith(";BRIDGE")
    
def is_end_bridge(line: str) -> bool:
    return line.startswith(";MESH") or line.startswith(";TIME") or line.startswith(";LAYER")

def is_extrusion_line(line: str) -> bool:
    return "G1" in line and "X" in line and "Y" in line and "E" in line

def get_type(line: str) -> str:
    the_type = 'none'
    if(line.startswith(";TYPE")):
        the_type = line[6:]
    return the_type
    
class AdvancedBridges(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "AdvancedBridges",
            "key": "AdvancedBridges",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "do_pauses":
                {
                    "label": "Делать паузы",
                    "description": "Делать паузы перед каждым мостом",
                    "type": "bool",
                    "default_value": true
                },
                "delay_time":
                {
                    "label": "Время задержки",
                    "description": "Время задержки перед каждым мостом в миллисекундах",
                    "type": "int",
                    "unit": "ms",
                    "default_value": 300,
                    "minimum_value": 10,
                    "maximum_value": 10000,
                    "maximum_value_warning": 5000
                },
                "play_tone":
                {
                    "label": "Включить звук",
                    "description": "Издавать звук перед каждым мостом",
                    "type": "bool",
                    "default_value": true
                },
                "tone_time":
                {
                    "label": "Длительность сигнала",
                    "description": "Длительность сигнала в миллисекундах",
                    "type": "int",
                    "unit": "ms",
                    "default_value": 100,
                    "minimum_value": 10,
                    "maximum_value": 10000,
                    "maximum_value_warning": 1000
                },
                "tone_freq":
                {
                    "label": "Частота сигнала",
                    "description": "Издавать звук с определенной частотой",
                    "type": "int",
                    "unit": "Hz",
                    "default_value": 1318,
                    "minimum_value": 10,
                    "maximum_value": 20000,
                    "maximum_value_warning": 16000
                },
                "set_speed":
                {
                    "label": "Задать скорость",
                    "description": "Переопределить параметр G1 F[]",
                    "type": "bool",
                    "default_value": true
                },
                "new_speed":
                {
                    "label": "Новая скорость",
                    "description": "Подача будет установлена на указанное значение",
                    "type": "int",
                    "unit": "F",
                    "default_value": 100,
                    "minimum_value": 1,
                    "maximum_value": 10000,
                    "maximum_value_warning": 2000
                },
                "mul_speed":
                {
                    "label": "Умножить скорость",
                    "description": "Умножить параметр G1 F[]",
                    "type": "bool",
                    "default_value": false
                },
                "mul_speed_k":
                {
                    "label": "Коэффициент подачи",
                    "description": "Скорость печати мостов будет умножена на указанное значение",
                    "type": "float",
                    "unit": "%",
                    "default_value": 50,
                    "minimum_value": 1,
                    "maximum_value": 100,
                    "maximum_value_warning": 101
                },
                "set_flow":
                {
                    "label": "Задать поток",
                    "description": "Переопределить параметр G1 E[]",
                    "type": "bool",
                    "default_value": false
                },
                "new_flow":
                {
                    "label": "Новое значение потока",
                    "description": "Поток печати мостов будет установлен на указанное значение",
                    "type": "float",
                    "unit": "E",
                    "default_value": 0.01,
                    "minimum_value": 0,
                    "maximum_value": 10,
                    "maximum_value_warning": 2
                },
                "mul_flow":
                {
                    "label": "Умножить поток",
                    "description": "Умножить параметр G1 E[]",
                    "type": "bool",
                    "default_value": true
                },
                "mul_flow_k":
                {
                    "label": "Коэффециент потока",
                    "description": "Поток печати мостов будет умножен на указанное значение",
                    "type": "float",
                    "unit": "%",
                    "default_value": 50,
                    "minimum_value": 1,
                    "maximum_value": 100,
                    "maximum_value_warning": 101
                },
                "use_retract":
                {
                    "label": "Разрешить откат",
                    "description": "Втягивать пластик перед мостом",
                    "type": "bool",
                    "default_value": true
                },
                "retract_value":
                {
                    "label": "Величина отката",
                    "description": "Длина нити материала, которая будет извлечена во время отката",
                    "type": "float",
                    "unit": "mm",
                    "default_value": 4,
                    "minimum_value": 0,
                    "maximum_value": 20,
                    "maximum_value_warning": 10
                }
            }
        }"""

    def execute(self, data):

        prop_do_pauses = bool(self.getSettingValueByKey("do_pauses"))
        prop_delay_time = int(self.getSettingValueByKey("delay_time"))

        prop_play_tone = bool(self.getSettingValueByKey("play_tone"))
        prop_tone_time = int(self.getSettingValueByKey("tone_time"))
        prop_tone_freq = int(self.getSettingValueByKey("tone_freq"))

        prop_set_speed = bool(self.getSettingValueByKey("set_speed"))
        prop_new_speed = int(self.getSettingValueByKey("new_speed"))
        prop_mul_speed = bool(self.getSettingValueByKey("mul_speed"))
        prop_mul_speed_k = float(self.getSettingValueByKey("mul_speed_k")) / 100

        prop_set_flow = bool(self.getSettingValueByKey("set_flow"))
        prop_new_flow = float(self.getSettingValueByKey("new_flow"))
        prop_mul_flow = bool(self.getSettingValueByKey("mul_flow"))
        prop_mul_flow_k = float(self.getSettingValueByKey("mul_flow_k")) / 100

        prop_use_retract = bool(self.getSettingValueByKey("use_retract"))
        prop_retract_value = float(self.getSettingValueByKey("retract_value"))

        # pauses and tone
        delay_instruction = ""
        if prop_do_pauses:
            if prop_play_tone:
                delay_instruction += "M300 P{} S{} ; play tone ".format(str(prop_tone_time), str(prop_tone_freq))
            delay_instruction += "\nG4 P{} ; delay ".format(str(prop_delay_time))

        previous_E = 0

        new_data = []

        for layer_index, layer in enumerate(data):
            is_a_bridge = False
            current_type = 'initial'
            
            lines = layer.split("\n")
            for line_index, line in enumerate(lines):

                # new_line = line[line_index]

                if is_begin_bridge(line):
                    if not is_a_bridge:
                        lines[line_index] += "\n;START_BRIDGE"
                        # new_line += "\n;START_BRIDGE"
                    is_a_bridge = True

                if is_end_bridge(line):
                    if is_a_bridge:
                        lines[line_index] += "\n;END_BRIDGE"
                        # new_line += "\n;END_BRIDGE"
                    is_a_bridge = False
                
                if get_type(line) != 'none':
                    current_type = get_type(line)

                target_type = current_type == 'WALL-OUTER' or current_type == 'initial'

                # change speed
                if is_a_bridge and target_type and is_extrusion_line(line):
                    # new_line = ""
                    lines[line_index] = ""
                    # pauses
                    # new_line += delay_instruction
                    lines[line_index] += delay_instruction
                    # extrusion
                    searchF = re.search(r"F(\d*\.?\d*)", line)
                    searchE = re.search(r"E(\d*\.?\d*)", line)
                    searchX = re.search(r"X(\d*\.?\d*)", line)
                    searchY = re.search(r"Y(\d*\.?\d*)", line)
                    if searchF and searchE:
                        # SPEED
                        old_f_instruction = "F" + str(searchF.group(1))
                        current_F = float(searchF.group(1)[1:])
                        # set speed
                        if prop_set_speed:
                            new_F = prop_new_speed
                        # multiply speed
                        if prop_mul_speed:
                            new_F = current_F * prop_mul_speed_k

                        new_f_instruction = "F{:.0f}".format(new_F)

                        # FLOW
                        old_e_instruction = "E" + str(searchE.group(1))
                        current_E = float(searchE.group(1)[1:])
                        # set flow
                        if prop_set_flow:
                            new_E = prop_new_flow
                        # multiply flow
                        if prop_mul_flow:
                            delta_E = current_E - previous_E
                            new_E = delta_E * prop_mul_flow_k

                        new_e_instruction = "E{:.5f}".format(new_E)

                        # APPLY
                        # new_line = ""
                        # set extruder to relative
                        lines[line_index] += "\nM83 ; set extruder to relative"
                        # new_line += "\nM83 ; set extruder to relative"
                        # set flow
                        # g1_pos = lines[line_index].find("G1")
                        # g1_end = lines[line_index].find("\n", g1_pos)
                        # lines[line_index]
                        lines[line_index] += "\n" + line[:].replace(old_f_instruction, new_f_instruction).replace(old_e_instruction, new_e_instruction) + " ; FLOW CHANGED"
                        # new_line += lines[line_index][:].replace(old_f_instruction, new_f_instruction).replace(old_e_instruction, new_e_instruction) + " ; FLOW CHANGED"
                        # lines[line_index] += "G1 {} {} {} {} ; FLOW CHANGED".format(new_f_instruction, searchX, searchY, new_e_instruction)
                        # new_line += "G1 {} {} {} {} ; FLOW CHANGED".format(new_f_instruction, searchX, searchY, new_e_instruction)
                        # set extruder to absolute
                        lines[line_index] += "\nM82 ; set extruder to absolute"
                        # new_line += "\nM82 ; set extruder to absolute"
                        # set extruder position
                        lines[line_index] += "\nG92 {} ; set extruder position".format(old_e_instruction)
                        # new_line += "\nG92 {} ; set extruder position".format(old_e_instruction)

                # save last extruder position
                if is_extrusion_line(line):
                    previous_E = float(re.search(r"E(\d*\.?\d*)", line).group(1)[1:])

                # lines[line_index] = new_line

                        
            result = "\n".join(lines)
            data[layer_index] = result

        return data