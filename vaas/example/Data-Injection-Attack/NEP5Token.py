"""
NEP5 Token
===================================


.. moduleauthor:: Thomas Saunders <tom@cityofzion.io>

This file, when compiled to .avm format, would comply with the current NEP5 token standard on the NEO blockchain

Token standard is available in proposal form here:
`NEP5 Token Standard Proposal <https://github.com/neo-project/proposals/blob/master/nep-5.mediawiki>`_

Or, from within the neo-python shell
``build path/to/NEP5.py test 0710 05 True name []``


Below is the current implementation in Python


"""

from DNA.interop.System.Runtime import Log, CheckWitness
from DNA.interop.System.Action import RegisterAction
from DNA.interop.System.Storage import GetContext, Get, Put, Delete
from DNA.builtins import concat
from DNA.builtins import *

DispatchTransferEvent = RegisterAction('transfer', 'from', 'to', 'amount')

DispatchApproveEvent = RegisterAction('approval', 'owner', 'spender', 'value')


def Main(operation, args):
    """
    This is the main entry point for the Smart Contract

    :param operation: the operation to be performed ( eg `balanceOf`, `transfer`, etc)
    :type operation: str
    :param args: a list of arguments ( which may be empty, but not absent )
    :type args: list
    :return: indicating the successful execution of the smart contract
    :rtype: bool
    """
    if operation == 'transfer':
        if len(args) == 3:
            t_from = args[0]
            t_to = args[1]
            t_amount = args[2]
            transfer = DoTransfer(t_from, t_to, t_amount)
            return transfer
        else:
            return False

    elif operation == 'transferFrom':
        if len(args) == 3:
            t_from = args[0]
            t_to = args[1]
            t_amount = args[2]
            transfer = DoTransferFrom(t_from, t_to, t_amount)
            return transfer
        return False

    elif operation == 'approve':
        if len(args) == 3:
            t_owner = args[0]
            t_spender = args[1]
            t_amount = args[2]
            approve = DoApprove(t_owner, t_spender, t_amount)
            return approve
        return False

    elif operation == 'allowance':
        if len(args) == 2:
            t_owner = args[0]
            t_spender = args[1]
            amount = GetAllowance(t_owner, t_spender)
            return amount
        return False

    result = 'unknown operation'

    return result



def DoTransfer(t_from, t_to, amount):
    """
    Method to transfer NEP5 tokens of a specified amount from one account to another

    :param t_from: the address to transfer from
    :type t_from: bytearray
    :param t_to: the address to transfer to
    :type t_to: bytearray
    :param amount: the amount of NEP5 tokens to transfer
    :type amount: int

    :return: whether the transfer was successful
    :rtype: bool

    """
    if amount <= 0:
        ##Log("Cannot transfer negative amount")
        return False

    from_is_sender = CheckWitness(t_from)

    if not from_is_sender:
        ##Log("Not owner of funds to be transferred")
        return False

    if t_from == t_to:
        ##Log("Sending funds to self")
        return True

    context = GetContext()

    from_val = Get(context, t_from)

    if from_val < amount:
        ##Log("Insufficient funds to transfer")
        return False

    if from_val == amount:
        Delete(context, t_from)

    else:
        difference = from_val - amount
        Put(context, t_from, difference)

    to_value = Get(context, t_to)

    to_total = to_value + amount

    Put(context, t_to, to_total)

    DispatchTransferEvent(t_from, t_to, amount)

    return True


def DoTransferFrom(t_from, t_to, amount):
    """
    Method to transfer NEP5 tokens of a specified amount from one account to another

    :param t_from: the address to transfer from
    :type t_from: bytearray
    :param t_to: the address to transfer to
    :type t_to: bytearray
    :param amount: the amount of NEP5 tokens to transfer
    :type amount: int

    :return: whether the transfer was successful
    :rtype: bool

    """
    if amount <= 0:
        return False

    context = GetContext()

    allowance_key = concat(t_from, t_to)

    available_to_to_addr = Get(context, allowance_key)

    if available_to_to_addr < amount:
        #Log("Insufficient funds approved")
        return False

    from_balance = Get(context, t_from)

    if from_balance < amount:
        #Log("Insufficient tokens in from balance")
        return False

    to_balance = Get(context, t_to)

    # calculate the new balances
    new_from_balance = from_balance - amount
    new_to_balance = to_balance + amount
    new_allowance = available_to_to_addr - amount

    # persist the new balances
    Put(context, allowance_key, new_allowance)
    Put(context, t_to, new_to_balance)
    Put(context, t_from, new_from_balance)

    #Log("transfer complete")

    # dispatch transfer event
    DispatchTransferEvent(t_from, t_to, amount)

    return True


def DoApprove(t_owner, t_spender, amount):
    """

    Method by which the owner of an address can approve another address
    ( the spender ) to spend an amount

    :param t_owner: Owner of tokens
    :type t_owner: bytearray
    :param t_spender: Requestor of tokens
    :type t_spender: bytearray
    :param amount: Amount requested to be spent by Requestor on behalf of owner
    :type amount: bytearray

    :return: success of the operation
    :rtype: bool

    """

    owner_is_sender = CheckWitness(t_owner)

    if not owner_is_sender:
        #Log("Incorrect permission")
        return False

    context = GetContext()

    from_balance = Get(context, t_owner)

    # cannot approve an amount that is
    # currently greater than the from balance
    if from_balance >= amount:

        approval_key = concat(t_owner, t_spender)

        current_approved_balance = Get(context, approval_key)

        new_approved_balance = current_approved_balance + amount

        Put(context, approval_key, new_approved_balance)

        #Log("Approved")

        DispatchApproveEvent(t_owner, t_spender, amount)

        return True

    return False


def GetAllowance(t_owner, t_spender):
    """
    Gets the amount of tokens that a spender is allowed to spend
    from the owners' account.

    :param t_owner: Owner of tokens
    :type t_owner: bytearray
    :param t_spender: Requestor of tokens
    :type t_spender: bytearray

    :return: Amount allowed to be spent by Requestor on behalf of owner
    :rtype: int

    """

    context = GetContext()

    allowance_key = concat(t_owner, t_spender)

    amount = Get(context, allowance_key)

    return amount

