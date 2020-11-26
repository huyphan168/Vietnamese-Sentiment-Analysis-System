const mongoose = require("mongoose");
const { db } = require("./category");
const { ObjectId } = mongoose.Schema;

const userSchema = new mongoose.Schema(
  {
    name: String,
    email: {
      type: String,
      required: true,
      index: true,
    },

    campaigns: {
      type: Array,
      default: [
      ],
    },

    address: String,
  },
  { timestamps: true }
);

module.exports = mongoose.model("User", userSchema);
