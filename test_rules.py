TEST_RULES = {

    "Primary Cold Static": {
        "rpm": 0,
        "temperature": "AMB",
        "mode": 1
    },

    "Secondary Cold Static": {
        "rpm": 0,
        "temperature": "AMB",
        "mode": 2
    },

    "MRT Test": {
        "rpm": 0,
        "temperature": ">160",
        "mode": 1,
        "torque": 1
    },

    "Primary Dynamic": {
        "temperature": ">160",
        "secondary_fixed": 1,
        "mode": 1
    },

    "Primary Hot Static": {
        "rpm": 0,
        "temperature": ">160",
        "mode": 1
    }

}
