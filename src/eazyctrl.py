"""
Tools for monitoring and controlling Eazy Controls KWL (air
exchanger) devices via Modbus/TCP.
"""
import random
import socket
import struct


_MODBUS_TCP_PORT = 502

_RECV_BUFFER_SIZE = 1024

_SOCKET_TIMEOUT = 10.0


_KWL_FEATURES = {
    'fan_stage': ("v00102", 1, int, str),
    'temperature_outside_air': ("v00104", 7, float, None),
    'temperature_supply_air': ("v00105", 7, float, None),
    'temperature_outgoing_air': ("v00106", 7, float, None),
    'temperature_extract_air': ("v00107", 7, float, None),
}

_KWL_UNIT_ID = 180

def _char_to_bytes(val):
    return struct.pack('B', val)

def _bytes_to_char(val):
    return struct.unpack('B', val)[0]

def _short_to_bytes(val):
    return struct.pack('>H', val)

def _bytes_to_short(val):
    return struct.unpack('>H', val)[0]

def _bytes_to_bytes(val):
    return val

_FIELDS_HEADER = {
    'transaction_identifier': ((0, 2), (_short_to_bytes, _bytes_to_short)),
    'protocol_identifier': ((2, 4), (_short_to_bytes, _bytes_to_short)),
    'length': ((4, 6), (_short_to_bytes, _bytes_to_short)),
    'unit_identifier': ((6, 7), (_char_to_bytes, _bytes_to_char)),
    'application_data': ((7, None), (_bytes_to_bytes, _bytes_to_bytes)),
}

_FIELDS_03_REQUEST_PDU = {
    'function_code': ((7, 8), (_char_to_bytes, _bytes_to_char)),
    'starting_address': ((8, 10), (_short_to_bytes, _bytes_to_short)),
    'quantity_of_registers': ((10, 12), (_short_to_bytes, _bytes_to_short)),
}

_FIELDS_03_REQUEST = dict(
    list(_FIELDS_HEADER.items()) + list(_FIELDS_03_REQUEST_PDU.items()))

_FIELDS_03_RESPONSE_PDU = {
    'function_code': ((7, 8), (_char_to_bytes, _bytes_to_char)),
    'byte_count': ((8, 9), (_char_to_bytes, _bytes_to_char)),
    'registers_value': ((9, None), (_bytes_to_bytes, _bytes_to_bytes)),
}

_FIELDS_03_RESPONSE = dict(
    list(_FIELDS_HEADER.items()) + list(_FIELDS_03_RESPONSE_PDU.items()))

_FIELDS_16_REQUEST_PDU = {
    'function_code': ((7, 8), (_char_to_bytes, _bytes_to_char)),
    'starting_address': ((8, 10), (_short_to_bytes, _bytes_to_short)),
    'quantity_of_registers': ((10, 12), (_short_to_bytes, _bytes_to_short)),
    'byte_count': ((12, 13), (_char_to_bytes, _bytes_to_char)),
    'registers_value': ((13, None), (_bytes_to_bytes, _bytes_to_bytes)),
}

_FIELDS_16_REQUEST = dict(
    list(_FIELDS_HEADER.items()) + list(_FIELDS_16_REQUEST_PDU.items()))


_FIELDS_16_RESPONSE_PDU = {
    'function_code': ((7, 8), (_char_to_bytes, _bytes_to_char)),
    'starting_address': ((8, 10), (_short_to_bytes, _bytes_to_short)),
    'quantity_of_registers': ((10, 12), (_short_to_bytes, _bytes_to_short)),
}

_FIELDS_16_RESPONSE = dict(
    list(_FIELDS_HEADER.items()) + list(_FIELDS_16_RESPONSE_PDU.items()))

_FIELDS_ERROR_PDU = {
    'error_code': ((7, 8), (_char_to_bytes, _bytes_to_char)),
    'exception_code': ((8, 9), (_char_to_bytes, _bytes_to_char)),
}

_FIELDS_ERROR = dict(
    list(_FIELDS_HEADER.items()) + list(_FIELDS_ERROR_PDU.items()))


class NamedByteArray(bytearray):

    def __init__(self, fields, minsize, template=None):
        self._fields = fields
        self._minsize = minsize
        if template is None:
            super().__init__(self._minsize)
        else:
            super().__init__(template)


    def __setitem__(self, fieldname, fieldvalue):
        if isinstance(fieldname, str):
            start, end, convfunc, _ = self._get_field_params(fieldname)
            super().__setitem__(slice(start, end), convfunc(fieldvalue))
        else:
            super().__setitem__(fieldname, fieldvalue)


    def __getitem__(self, fieldname):
        if isinstance(fieldname, str):
            start, end, _, convfunc = self._get_field_params(fieldname)
            return convfunc(super().__getitem__(slice(start, end)))
        else:
            return super().__getitem__(fieldname)


    def _get_field_params(self, fieldname):
        fieldparams = self._fields.get(fieldname)
        if fieldparams is None:
            raise ValueError("Invalid field name '" + fieldname + "'")
        start, end = fieldparams[0]
        setconv, getconv = fieldparams[1]
        return start, end, setconv, getconv



class ModbusMessage(NamedByteArray):

    def __init__(self, fields, minsize, template=None):
        super().__init__(fields, minsize, template)
        self._update_length()


    def __setitem__(self, fieldname, fieldvalue):
        super().__setitem__(fieldname, fieldvalue)
        self._update_length()


    def _update_length(self):
        super().__setitem__('length', len(self) - 6)



class Modbus03Request(ModbusMessage):

    def __init__(self, template=None):
        super().__init__(_FIELDS_03_REQUEST, 12, template)
        if template is None:
            self['function_code'] = 3


class Modbus03Response(ModbusMessage):

    def __init__(self, template=None):
        super().__init__(_FIELDS_03_RESPONSE, 9, template)
        if template is None:
            self['function_code'] = 3


class Modbus16Request(ModbusMessage):

    def __init__(self, template=None):
        super().__init__(_FIELDS_16_REQUEST, 11, template)
        if template is None:
            self['function_code'] = 16


class Modbus16Response(ModbusMessage):

    def __init__(self, template=None):
        super().__init__(_FIELDS_16_RESPONSE, 12, template)
        if template is None:
            self['function_code'] = 16


class ModbusError(ModbusMessage):

    def __init__(self, template=None, errorcode=None):
        super().__init__(_FIELDS_ERROR, 9, template)
        if errorcode is not None:
            self['error_code'] = errorcode


class EazyCommunicator:

    def __init__(self, server, port=_MODBUS_TCP_PORT, timeout=_SOCKET_TIMEOUT):
        self._transid = random.randrange(0, 2**16)
        self._server = server
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((server, port))
        self._socket.settimeout(timeout)


    def close(self):
        self._socket.shutdown(socket.SHUT_RD)
        self._socket.close()


    def write_variable(self, vardef):
        # Transmitted data must be rounded up to even bytes
        vardeflen = len(vardef)
        datalen = (vardeflen + 2) // 2  * 2
        data = bytearray(datalen)
        data[:vardeflen] = bytearray(vardef, encoding='ascii')

        self._transid += 1
        sendmsg = Modbus16Request()
        sendmsg['transaction_identifier'] = self._transid
        sendmsg['unit_identifier'] = _KWL_UNIT_ID
        sendmsg['starting_address'] = 1
        sendmsg['quantity_of_registers'] = datalen // 2
        sendmsg['byte_count'] = datalen
        sendmsg['registers_value'] = data
        self._socket.sendall(sendmsg)

        response = self._socket.recv(_RECV_BUFFER_SIZE)
        respmsg = Modbus16Response(template=response)
        if respmsg['function_code'] != 16:
            respmsg = ModbusError(template=response)
            print('Exception', respmsg['exception_code'])


    def read_variable(self, varname, varlen):

        answerlen = len(varname) + 1 + varlen
        datalen = (answerlen + 2) // 2 * 2

        self._transid += 1
        sendmsg = Modbus03Request()
        sendmsg['transaction_identifier'] = self._transid
        sendmsg['unit_identifier'] = _KWL_UNIT_ID
        sendmsg['starting_address'] = 1
        sendmsg['quantity_of_registers'] = datalen // 2
        self._socket.sendall(sendmsg)

        response = self._socket.recv(_RECV_BUFFER_SIZE)
        respmsg = Modbus03Response(template=response)
        if respmsg['function_code'] != 3:
            respmsg = ModbusError(template=response)
            print('Exception:', respmsg['exception_code'])
            return None
        else:
            answer = respmsg['registers_value'][len(varname) + 1 :]
            return answer.rstrip(b'\x00').decode('ascii')


class EazyController:

    def __init__(self, server):
        self._comm = EazyCommunicator(server)


    def close(self):
        self._comm.close()


    def get_variable(self, varname, varlen, convfunc=None):
        self._comm.write_variable(varname)
        answer = self._comm.read_variable(varname, varlen)
        if convfunc is None:
            return answer
        else:
            return convfunc(answer)


    def set_variable(self, varname, varval, convfunc=None):
        if convfunc is None:
            varcontent = varval
        elif isinstance(convfunc, str):
            varcontent = convfunc.format(varval)
        else:
            varcontent = convfunc(varval)
        vardef = "{}={}".format(varname, varcontent)
        self._comm.write_variable(vardef)


    def get_feature(self, feature):
        featureparams = _KWL_FEATURES.get(feature)
        if feature is None:
            raise ValueError("Unknown feature '" + feature + "'")
        varname, varlen, getconv, _ = featureparams
        return self.get_variable(varname, varlen, getconv)


    def set_feature(self, feature, featureval):
        featureparams = _KWL_FEATURES.get(feature)
        if feature is None:
            raise ValueError("Unknown feature '" + feature + "'")
        varname, _, _, setconv = featureparams
        if setconv is None:
            raise ValueError("Feature '" + feature + "' is read-only")
        self.set_variable(varname, featureval, setconv)
