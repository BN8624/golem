// 전술 커널 시나리오 세계(계약 고정·하네스 주입). getScenario(n)은 1-based n번 세계를 반환한다.
const SCENARIOS = [
  {
    "initialState": {
      "hero": {
        "hp": 100,
        "atk": 20,
        "pos": [
          0,
          0
        ]
      },
      "enemies": [
        {
          "id": "E1",
          "hp": 50,
          "atk": 10,
          "pos": [
            1,
            0
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "attack",
        "target": "E1"
      },
      {
        "type": "attack",
        "target": "E1"
      },
      {
        "type": "attack",
        "target": "E1"
      }
    ]
  },
  {
    "initialState": {
      "hero": {
        "hp": 20,
        "atk": 10,
        "pos": [
          0,
          0
        ]
      },
      "enemies": [
        {
          "id": "E1",
          "hp": 100,
          "atk": 30,
          "pos": [
            1,
            0
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "attack",
        "target": "E1"
      }
    ]
  },
  {
    "initialState": {
      "hero": {
        "hp": 1,
        "atk": 10,
        "pos": [
          0,
          0
        ]
      },
      "enemies": [
        {
          "id": "E1",
          "hp": 100,
          "atk": 50,
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
          1,
          0
        ]
      }
    ]
  },
  {
    "initialState": {
      "hero": {
        "hp": 100,
        "atk": 20,
        "pos": [
          0,
          0
        ]
      },
      "enemies": []
    },
    "actions": [
      {
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
      "hero": {
        "hp": 10,
        "atk": 20,
        "pos": [
          0,
          0
        ]
      },
      "enemies": [
        {
          "id": "E1",
          "hp": 10,
          "atk": 20,
          "pos": [
            1,
            0
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "attack",
        "target": "E1"
      }
    ]
  },
  {
    "initialState": {
      "hero": {
        "hp": 20,
        "atk": 20,
        "pos": [
          0,
          0
        ]
      },
      "enemies": [
        {
          "id": "E1",
          "hp": 20,
          "atk": 20,
          "pos": [
            1,
            0
          ]
        }
      ]
    },
    "actions": [
      {
        "type": "attack",
        "target": "E1"
      }
    ]
  }
];
exports.getScenario = (n) => SCENARIOS[n - 1] || null;
