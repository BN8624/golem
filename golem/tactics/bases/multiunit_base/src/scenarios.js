// 전술 커널 시나리오 세계(계약 고정·하네스 주입). getScenario(n)은 1-based n번 세계를 반환한다.
const SCENARIOS = [
  {
    "initialState": {
      "hero": {
        "hp": 10,
        "atk": 3,
        "pos": [
          0,
          0
        ]
      },
      "gridSize": 5,
      "enemies": [
        {
          "id": 1,
          "hp": 5,
          "atk": 2,
          "pos": [
            4,
            0
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "move",
        "dir": [
          0,
          1
        ]
      },
      {
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
      "hero": {
        "hp": 10,
        "atk": 3,
        "pos": [
          0,
          0
        ]
      },
      "gridSize": 5,
      "enemies": [
        {
          "id": 1,
          "hp": 5,
          "atk": 2,
          "pos": [
            2,
            0
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "move",
        "dir": [
          0,
          1
        ]
      },
      {
        "type": "move",
        "dir": [
          0,
          1
        ]
      },
      {
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
      "hero": {
        "hp": 10,
        "atk": 5,
        "pos": [
          0,
          0
        ]
      },
      "gridSize": 5,
      "enemies": [
        {
          "id": 1,
          "hp": 5,
          "atk": 2,
          "pos": [
            1,
            0
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "attack"
      }
    ]
  },
  {
    "initialState": {
      "hero": {
        "hp": 3,
        "atk": 1,
        "pos": [
          1,
          1
        ]
      },
      "gridSize": 5,
      "enemies": [
        {
          "id": 1,
          "hp": 9,
          "atk": 2,
          "pos": [
            0,
            1
          ]
        },
        {
          "id": 2,
          "hp": 9,
          "atk": 2,
          "pos": [
            1,
            0
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "attack"
      }
    ]
  },
  {
    "initialState": {
      "hero": {
        "hp": 20,
        "atk": 3,
        "pos": [
          2,
          2
        ]
      },
      "gridSize": 5,
      "enemies": [
        {
          "id": 1,
          "hp": 5,
          "atk": 1,
          "pos": [
            0,
            2
          ]
        },
        {
          "id": 2,
          "hp": 5,
          "atk": 1,
          "pos": [
            4,
            2
          ]
        }
      ]
    },
    "actions": [
      {
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
      "hero": {
        "hp": 10,
        "atk": 3,
        "pos": [
          0,
          0
        ]
      },
      "gridSize": 5,
      "enemies": [
        {
          "id": 1,
          "hp": 5,
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
      "hero": {
        "hp": 10,
        "atk": 3,
        "pos": [
          2,
          0
        ]
      },
      "gridSize": 3,
      "enemies": [
        {
          "id": 1,
          "hp": 5,
          "atk": 2,
          "pos": [
            0,
            0
          ]
        },
        {
          "id": 2,
          "hp": 5,
          "atk": 2,
          "pos": [
            1,
            0
          ]
        }
      ]
    },
    "actions": [
      {
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
      "hero": {
        "hp": 15,
        "atk": 5,
        "pos": [
          0,
          0
        ]
      },
      "gridSize": 5,
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
            4,
            4
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "attack"
      },
      {
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
      "hero": {
        "hp": 10,
        "atk": 3,
        "pos": [
          0,
          0
        ]
      },
      "gridSize": 6,
      "enemies": [
        {
          "id": 1,
          "hp": 9,
          "atk": 1,
          "pos": [
            5,
            5
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "move",
        "dir": [
          1,
          0
        ]
      }
    ]
  }
];
exports.getScenario = (n) => SCENARIOS[n - 1] || null;
