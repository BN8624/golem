// 전술 커널 시나리오 세계(계약 고정·하네스 주입). getScenario(n)은 1-based n번 세계를 반환한다.
const SCENARIOS = [
  {
    "initialState": {
      "gridSize": 6,
      "allies": [
        {
          "id": 1,
          "hp": 10,
          "atk": 3,
          "pos": [
            0,
            0
          ]
        },
        {
          "id": 2,
          "hp": 10,
          "atk": 3,
          "pos": [
            4,
            4
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 8,
          "atk": 2,
          "pos": [
            5,
            5
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 1,
        "type": "move",
        "dir": [
          1,
          0
        ]
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 5,
      "allies": [
        {
          "id": 1,
          "hp": 10,
          "atk": 3,
          "pos": [
            0,
            1
          ]
        },
        {
          "id": 2,
          "hp": 10,
          "atk": 3,
          "pos": [
            2,
            1
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 6,
          "atk": 1,
          "pos": [
            1,
            1
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 1,
        "type": "attack"
      },
      {
        "unit": 2,
        "type": "attack"
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 5,
      "allies": [
        {
          "id": 1,
          "hp": 3,
          "atk": 1,
          "pos": [
            2,
            2
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 9,
          "atk": 2,
          "pos": [
            1,
            2
          ]
        },
        {
          "id": 2,
          "hp": 9,
          "atk": 2,
          "pos": [
            3,
            2
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 1,
        "type": "attack"
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 7,
      "allies": [
        {
          "id": 1,
          "hp": 12,
          "atk": 3,
          "pos": [
            0,
            0
          ]
        },
        {
          "id": 2,
          "hp": 12,
          "atk": 3,
          "pos": [
            6,
            6
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 8,
          "atk": 1,
          "pos": [
            2,
            0
          ]
        },
        {
          "id": 2,
          "hp": 8,
          "atk": 1,
          "pos": [
            6,
            4
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 1,
        "type": "move",
        "dir": [
          0,
          1
        ]
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 5,
      "allies": [
        {
          "id": 1,
          "hp": 10,
          "atk": 3,
          "pos": [
            0,
            2
          ]
        },
        {
          "id": 2,
          "hp": 10,
          "atk": 3,
          "pos": [
            4,
            2
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 8,
          "atk": 1,
          "pos": [
            2,
            2
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 2,
        "type": "move",
        "dir": [
          0,
          1
        ]
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 5,
      "allies": [
        {
          "id": 1,
          "hp": 10,
          "atk": 3,
          "pos": [
            1,
            1
          ]
        },
        {
          "id": 2,
          "hp": 10,
          "atk": 3,
          "pos": [
            2,
            1
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 9,
          "atk": 1,
          "pos": [
            4,
            4
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 1,
        "type": "move",
        "dir": [
          1,
          0
        ]
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 6,
      "allies": [
        {
          "id": 1,
          "hp": 10,
          "atk": 4,
          "pos": [
            0,
            0
          ]
        },
        {
          "id": 2,
          "hp": 10,
          "atk": 4,
          "pos": [
            0,
            1
          ]
        },
        {
          "id": 3,
          "hp": 10,
          "atk": 4,
          "pos": [
            0,
            2
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 6,
          "atk": 2,
          "pos": [
            3,
            0
          ]
        },
        {
          "id": 2,
          "hp": 6,
          "atk": 2,
          "pos": [
            3,
            2
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 1,
        "type": "move",
        "dir": [
          1,
          0
        ]
      },
      {
        "unit": 2,
        "type": "move",
        "dir": [
          1,
          0
        ]
      },
      {
        "unit": 3,
        "type": "move",
        "dir": [
          1,
          0
        ]
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 6,
      "allies": [
        {
          "id": 1,
          "hp": 12,
          "atk": 6,
          "pos": [
            0,
            0
          ]
        },
        {
          "id": 2,
          "hp": 12,
          "atk": 6,
          "pos": [
            5,
            5
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 5,
          "atk": 2,
          "pos": [
            1,
            0
          ]
        },
        {
          "id": 2,
          "hp": 5,
          "atk": 2,
          "pos": [
            3,
            5
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 1,
        "type": "attack"
      },
      {
        "unit": 2,
        "type": "move",
        "dir": [
          -1,
          0
        ]
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 8,
      "allies": [
        {
          "id": 1,
          "hp": 10,
          "atk": 3,
          "pos": [
            0,
            0
          ]
        },
        {
          "id": 2,
          "hp": 10,
          "atk": 3,
          "pos": [
            1,
            0
          ]
        }
      ],
      "enemies": [
        {
          "id": 1,
          "hp": 9,
          "atk": 1,
          "pos": [
            7,
            7
          ]
        }
      ]
    },
    "actions": [
      {
        "unit": 1,
        "type": "move",
        "dir": [
          1,
          0
        ]
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 5,
      "turn": 0,
      "allies": [
        {
          "id": 0,
          "hp": 10,
          "pos": [
            0,
            0
          ],
          "atk": 10,
          "range": 2
        }
      ],
      "enemies": [
        {
          "id": 0,
          "hp": 10,
          "pos": [
            0,
            2
          ],
          "atk": 5
        }
      ]
    },
    "actions": [
      {
        "unit": 0,
        "type": "attack"
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 5,
      "turn": 0,
      "allies": [
        {
          "id": 0,
          "hp": 10,
          "pos": [
            0,
            0
          ],
          "atk": 5,
          "range": 3
        }
      ],
      "enemies": [
        {
          "id": 0,
          "hp": 10,
          "pos": [
            0,
            3
          ],
          "atk": 5
        },
        {
          "id": 1,
          "hp": 10,
          "pos": [
            0,
            1
          ],
          "atk": 5
        }
      ]
    },
    "actions": [
      {
        "unit": 0,
        "type": "attack"
      }
    ]
  },
  {
    "initialState": {
      "gridSize": 5,
      "turn": 0,
      "allies": [
        {
          "id": 0,
          "hp": 10,
          "pos": [
            0,
            0
          ],
          "atk": 10,
          "range": 2
        }
      ],
      "enemies": [
        {
          "id": 0,
          "hp": 15,
          "pos": [
            0,
            2
          ],
          "atk": 5
        }
      ]
    },
    "actions": [
      {
        "unit": 0,
        "type": "attack"
      },
      {
        "unit": 0,
        "type": "attack"
      }
    ]
  }
];
exports.getScenario = (n) => SCENARIOS[n - 1] || null;
